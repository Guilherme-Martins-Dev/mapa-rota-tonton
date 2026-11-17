"""Atualização incremental do trânsito: consulta só alguns pontos e reescreve só o que mudou.

O refresh completo (pesos.atribuir_pesos + consumo.atribuir_consumo) refaz todas as arestas e
consulta todos os pontos médios. Aqui o grafo guarda dados de idades diferentes: cada ponto
tem o instante da última consulta bem-sucedida (`Indice.ultima`) e os mais antigos vão primeiro.
"""
import math
import time
from dataclasses import dataclass, field
from typing import Callable

from tonton.consumo import PADRAO, Veiculo, gravar_litros
from tonton.pesos import _velocidades_tomtom, gravar_velocidades
from tonton.ruas import eh_tomtom, ponto_medio

Aresta = tuple  # (u, v, chave)
PESOS_VARIAVEIS = ("t_livre", "t_atual", "litros")  # atributos que a atualização pode mudar


@dataclass
class Indice:
    arestas_por_ponto: dict = field(default_factory=dict)  # ponto -> [(u, v, chave)] (só TomTom)
    ultima: dict = field(default_factory=dict)             # ponto -> timestamp (0 = nunca)


@dataclass(frozen=True)
class Resultado:
    consultados: int                # consultas tentadas (inclui as que falharam)
    falhas: int                     # consultas que levantaram erro ou vieram incompletas
    alteradas: frozenset            # arestas (u, v, chave) reescritas
    pioraram: frozenset             # alteradas com t_atual maior
    melhoraram: frozenset           # alteradas com t_atual menor (ou que não tinham t_atual)
    pulados_por_orcamento: int      # pontos que ficaram para o próximo ciclo
    # Valores ANTERIORES dos pesos variáveis de cada aresta alterada: {aresta: {peso: valor}}.
    # Necessário porque litros e t_livre variam por conta própria (ver rota_continua_otima).
    anteriores: dict = field(default_factory=dict)


def indexar(G) -> Indice:
    """Agrupa as arestas TomTom pelo ponto médio (um ponto pode atender várias arestas)."""
    indice = Indice()
    for u, v, chave, dados in G.edges(keys=True, data=True):
        if not eh_tomtom(dados):
            continue
        ponto = ponto_medio(G, u, v, chave)
        indice.arestas_por_ponto.setdefault(ponto, []).append((u, v, chave))
        indice.ultima.setdefault(ponto, 0.0)
    return indice


def _mudou(dados: dict, v_livre: float, v_atual: float, tolerancia_kmh: float) -> bool:
    """True se a aresta nunca teve velocidades ou alguma difere por >= tolerancia_kmh."""
    ant_livre, ant_atual = dados.get("v_livre"), dados.get("v_atual")
    if ant_livre is None or ant_atual is None:
        return True
    return abs(v_livre - ant_livre) >= tolerancia_kmh or abs(v_atual - ant_atual) >= tolerancia_kmh


def atualizar_transito(G, indice: Indice, consultar: Callable[[float, float], dict],
                       veiculo: Veiculo = PADRAO, orcamento: int | None = None,
                       tolerancia_kmh: float = 1.0, agora: Callable[[], float] = time.time) -> Resultado:
    """Consulta até `orcamento` pontos (None = todos), os de `ultima` mais antiga primeiro
    (nunca consultados antes), e reescreve só as arestas cujas velocidades mudaram.

    - Falha (exceção ou resposta incompleta): a aresta MANTÉM o último valor conhecido. O
      fallback do OSM é uma estimativa sem trânsito; sobrescrever um dado real recente com ele
      faria a rota "esquecer" um congestionamento por causa de um erro de rede passageiro.
      O ponto não tem `ultima` atualizada, então volta ao começo da fila no próximo ciclo.
    - Mudança menor que `tolerancia_kmh` em v_livre e v_atual: nada é reescrito (evita recalcular
      por ruído); `ultima` é atualizada mesmo assim, pois a consulta deu certo.
    - Só os atributos das arestas alteradas mudam; G, `indice.arestas_por_ponto` ficam intactos
      (muda apenas `indice.ultima`).
    """
    ordem = sorted(indice.arestas_por_ponto, key=lambda p: indice.ultima.get(p, 0.0))  # estável
    escolhidos = ordem if orcamento is None else ordem[:max(orcamento, 0)]

    falhas = 0
    alteradas, pioraram, melhoraram, anteriores = set(), set(), set(), {}
    for ponto in escolhidos:
        try:
            velocidades = _velocidades_tomtom(consultar(*ponto))
        except Exception:
            velocidades = None
        if velocidades is None:
            falhas += 1
            continue
        v_livre, v_atual = velocidades
        indice.ultima[ponto] = agora()
        for aresta in indice.arestas_por_ponto[ponto]:
            dados = G.edges[aresta]
            if not _mudou(dados, v_livre, v_atual, tolerancia_kmh):
                continue
            antes = {p: dados.get(p, math.inf) for p in PESOS_VARIAVEIS}
            gravar_velocidades(dados, v_livre, v_atual)
            gravar_litros(dados, veiculo)
            alteradas.add(aresta)
            anteriores[aresta] = antes
            if dados["t_atual"] > antes["t_atual"]:
                pioraram.add(aresta)
            elif dados["t_atual"] < antes["t_atual"]:
                melhoraram.add(aresta)
    return Resultado(
        consultados=len(escolhidos), falhas=falhas, alteradas=frozenset(alteradas),
        pioraram=frozenset(pioraram), melhoraram=frozenset(melhoraram),
        pulados_por_orcamento=len(ordem) - len(escolhidos), anteriores=anteriores,
    )


def rota_continua_otima(G, rota, resultado: Resultado, peso: str) -> bool:
    """True se a rota, ótima ANTES da atualização, continua ótima sem rodar o Dijkstra de novo.

    Conservador: pode dizer False com a rota ainda ótima, nunca True com a rota já superada.
    Prova (pesos não negativos): seja R a rota e C seu custo antes. Para qualquer outra rota R',
    custo_antes(R') >= C. Se nenhuma aresta de R foi alterada, custo_depois(R) = C. Se toda
    aresta alterada fora de R só piorou ou ficou igual, custo_depois(R') >= custo_antes(R') >= C.
    Logo custo_depois(R') >= custo_depois(R): R segue ótima (pode haver empate).
    Se uma aresta de R mudou, o custo de R mudou; se uma de fora melhorou, pode ter surgido atalho.

    "Melhorou" é medido no próprio `peso` (t_atual, t_livre ou litros) pelos valores anteriores
    guardados no Resultado: litros não é monótono em t_atual (curva em U), então olhar só
    `melhoraram` (que é por t_atual) estaria errado para o consumo. `length` não muda com o
    trânsito: sempre True. Exige que `resultado` seja da atualização imediatamente anterior.
    """
    if peso == "length":
        return True
    na_rota = set(rota.arestas)
    if na_rota & resultado.alteradas:
        return False
    for aresta in resultado.alteradas:
        antes = resultado.anteriores[aresta].get(peso)
        if antes is None:  # peso que a atualização não controla: não dá para provar
            return False
        if G.edges[aresta].get(peso, math.inf) < antes:
            return False
    return True
