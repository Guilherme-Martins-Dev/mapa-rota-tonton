import copy
import math
import random

import networkx as nx
import pytest

from tonton.atualizacao import (
    Indice,
    Resultado,
    atualizar_transito,
    indexar,
    rota_continua_otima,
)
from tonton.consumo import PADRAO, atribuir_consumo
from tonton.pesos import atribuir_pesos
from tonton.rotas import menor_rota
from tonton.ruas import ponto_medio

PESOS_ATUALIZAVEIS = ("t_livre", "t_atual", "litros")


# ---------- utilidades ----------

def fluxo(livre, atual):
    return {"freeFlowSpeed": livre, "currentSpeed": atual}


def consultar_de(G, por_aresta, padrao=None):
    """consultar(lat, lon) falso: por_aresta {(u,v,k): (livre, atual)} -> resposta no ponto médio.

    Ponto sem resposta definida: `padrao` (livre, atual) se dado; senão levanta erro.
    """
    por_ponto = {ponto_medio(G, *a): fluxo(*va) for a, va in por_aresta.items()}

    def consultar(lat, lon):
        if (lat, lon) in por_ponto:
            return por_ponto[(lat, lon)]
        if padrao is not None:
            return fluxo(*padrao)
        raise RuntimeError("ponto sem resposta")

    chamadas = []

    def registrando(lat, lon):
        chamadas.append((lat, lon))
        return consultar(lat, lon)

    registrando.chamadas = chamadas
    return registrando


def preparar(G, consultar):
    atribuir_pesos(G, consultar)
    atribuir_consumo(G)
    return G


def grafo_reta():
    """A -> B (2 arestas paralelas primary + 1 residential no mesmo trecho), B -> C secondary,
    C -> D tertiary, D -> A residential, C -> A primary_link."""
    G = nx.MultiDiGraph()
    for no, (x, y) in {"A": (0.0, 0.0), "B": (0.01, 0.0), "C": (0.02, 0.0), "D": (0.02, 0.01)}.items():
        G.add_node(no, x=x, y=y)
    G.add_edge("A", "B", length=1000.0, highway="primary")
    G.add_edge("A", "B", length=1200.0, highway="primary")
    G.add_edge("A", "B", length=1000.0, highway="residential")  # mesmo ponto médio, não é TomTom
    G.add_edge("B", "C", length=800.0, highway=["secondary", "residential"], name=["X", "Y"])
    G.add_edge("C", "D", length=600.0, highway="tertiary")
    G.add_edge("D", "A", length=700.0, highway="residential")
    G.add_edge("C", "A", length=900.0, highway="primary_link")
    return G


def instantaneo(G):
    return {(u, v, k): copy.deepcopy(d) for u, v, k, d in G.edges(keys=True, data=True)}


# ---------- refatoração: mesmos atributos de antes ----------

def test_atribuir_pesos_e_consumo_iguais_ao_calculo_manual():
    from tonton.consumo import consumo_l_por_100km

    G = grafo_reta()
    por_aresta = {("A", "B", 0): (50.0, 30.0), ("B", "C", 0): (40.0, 20.0)}
    preparar(G, consultar_de(G, por_aresta, padrao=(60.0, 45.0)))
    for u, v, k, d in G.edges(keys=True, data=True):
        if (u, v, k) in por_aresta or (u, v) == ("A", "B"):  # A->B/1 divide o ponto de A->B/0
            livre, atual = por_aresta[(u, v, 0)] if (u, v) != ("A", "B") or k != 2 else (None, None)
            if k != 2:
                assert (d["v_livre"], d["v_atual"]) == (livre, atual)
        elif d["highway"] == "tertiary":
            assert (d["v_livre"], d["v_atual"]) == (60.0, 45.0)  # ponto sem resposta definida
        comp = d["length"]
        assert d["t_livre"] == pytest.approx(comp / (d["v_livre"] / 3.6))
        assert d["t_atual"] == pytest.approx(comp / (d["v_atual"] / 3.6))
        assert d["litros"] == pytest.approx(comp / 1000 * consumo_l_por_100km(d["v_atual"]) / 100)
    # vias fora da TomTom: fallback do OSM, v_atual == v_livre
    res = G.edges["A", "B", 2]
    assert res["v_livre"] == res["v_atual"] == 30.0
    assert G.edges["C", "A", 0]["v_livre"] == 30.0  # primary_link nunca vai para a TomTom


def test_gravar_velocidades_isolada_igual_a_atribuir_pesos():
    from tonton.pesos import gravar_velocidades

    dados = {"length": 360.0}
    gravar_velocidades(dados, 36.0, 18.0)
    assert dados == {"length": 360.0, "v_livre": 36.0, "v_atual": 18.0, "t_livre": 36.0, "t_atual": 72.0}


def test_gravar_velocidades_sem_length_vira_inf():
    from tonton.pesos import gravar_velocidades

    dados = {}
    gravar_velocidades(dados, 36.0, 18.0)
    assert dados["t_livre"] == math.inf and dados["t_atual"] == math.inf
    assert dados["v_livre"] == 36.0 and dados["v_atual"] == 18.0


def test_gravar_litros_isolada_igual_a_atribuir_consumo():
    from tonton.consumo import gravar_litros, litros

    dados = {"length": 2000.0, "v_atual": 65.0}
    gravar_litros(dados)
    assert dados["litros"] == pytest.approx(litros(2000.0, 65.0))
    # sem v_atual: velocidade livre do OSM
    dados = {"length": 1000.0, "highway": "primary"}
    gravar_litros(dados)
    assert dados["litros"] == pytest.approx(litros(1000.0, 50.0))
    # sem length: inf
    dados = {"v_atual": 40.0}
    gravar_litros(dados)
    assert dados["litros"] == math.inf


def test_atribuir_pesos_length_ausente_vira_inf():
    G = nx.MultiDiGraph()
    G.add_node(1, x=0, y=0)
    G.add_node(2, x=1, y=0)
    G.add_edge(1, 2, highway="residential")
    atribuir_pesos(G)
    atribuir_consumo(G)
    d = G.edges[1, 2, 0]
    assert d["t_livre"] == math.inf and d["t_atual"] == math.inf and d["litros"] == math.inf


# ---------- indexar ----------

def test_indexar_so_arestas_tomtom():
    G = grafo_reta()
    indice = indexar(G)
    indexadas = {a for lista in indice.arestas_por_ponto.values() for a in lista}
    assert indexadas == {("A", "B", 0), ("A", "B", 1), ("B", "C", 0), ("C", "D", 0)}
    assert ("A", "B", 2) not in indexadas      # residential
    assert ("C", "A", 0) not in indexadas      # primary_link
    assert ("D", "A", 0) not in indexadas


def test_indexar_mesmo_ponto_medio_na_mesma_lista():
    G = grafo_reta()
    indice = indexar(G)
    ponto_ab = ponto_medio(G, "A", "B", 0)
    assert ponto_medio(G, "A", "B", 1) == ponto_ab
    assert indice.arestas_por_ponto[ponto_ab] == [("A", "B", 0), ("A", "B", 1)]
    assert len(indice.arestas_por_ponto) == 3


def test_indexar_ultima_comeca_em_zero():
    indice = indexar(grafo_reta())
    assert set(indice.ultima) == set(indice.arestas_por_ponto)
    assert all(t == 0 for t in indice.ultima.values())


def test_indexar_grafo_sem_tomtom():
    G = nx.MultiDiGraph()
    G.add_node(1, x=0, y=0)
    G.add_node(2, x=1, y=0)
    G.add_edge(1, 2, length=10, highway="residential")
    indice = indexar(G)
    assert indice.arestas_por_ponto == {} and indice.ultima == {}


# ---------- atualizar_transito ----------

def grafo_quatro_pontos():
    """Quatro arestas TomTom isoladas (pontos distintos) + uma residential."""
    G = nx.MultiDiGraph()
    for i in range(5):
        G.add_node(i, x=0.01 * i, y=0.0)
    for i in range(4):
        G.add_edge(i, i + 1, length=1000.0 + i, highway="primary")
    G.add_edge(4, 0, length=500.0, highway="residential")
    return G


def test_ordem_por_ultima_nunca_consultados_primeiro():
    G = grafo_quatro_pontos()
    pontos = [ponto_medio(G, i, i + 1, 0) for i in range(4)]
    preparar(G, consultar_de(G, {}, padrao=(50.0, 40.0)))
    indice = indexar(G)
    indice.ultima.update({pontos[0]: 0.0, pontos[1]: 500.0, pontos[2]: 100.0, pontos[3]: 0.0})
    consultar = consultar_de(G, {}, padrao=(50.0, 40.0))
    atualizar_transito(G, indice, consultar, agora=lambda: 1000.0)
    assert consultar.chamadas == [pontos[0], pontos[3], pontos[2], pontos[1]]


def test_orcamento_limita_e_reporta_pulados():
    G = grafo_quatro_pontos()
    preparar(G, consultar_de(G, {}, padrao=(50.0, 40.0)))
    indice = indexar(G)
    consultar = consultar_de(G, {}, padrao=(50.0, 40.0))
    r = atualizar_transito(G, indice, consultar, orcamento=3, agora=lambda: 7.0)
    assert len(consultar.chamadas) == 3
    assert r.consultados == 3 and r.pulados_por_orcamento == 1


def test_orcamento_revezamento_cobre_todos_os_pontos():
    G = grafo_quatro_pontos()
    preparar(G, consultar_de(G, {}, padrao=(50.0, 40.0)))
    indice = indexar(G)
    consultar = consultar_de(G, {}, padrao=(50.0, 40.0))
    relogio = iter(range(1, 100))
    vistos = []
    for _ in range(2):
        antes = len(consultar.chamadas)
        atualizar_transito(G, indice, consultar, orcamento=2, agora=lambda: float(next(relogio)))
        vistos += consultar.chamadas[antes:]
    assert len(set(vistos)) == 4  # nenhum ponto repetido antes de todos serem consultados


def test_orcamento_none_consulta_todos():
    G = grafo_quatro_pontos()
    preparar(G, consultar_de(G, {}, padrao=(50.0, 40.0)))
    indice = indexar(G)
    consultar = consultar_de(G, {}, padrao=(50.0, 40.0))
    r = atualizar_transito(G, indice, consultar, orcamento=None)
    assert r.consultados == 4 and r.pulados_por_orcamento == 0
    assert len(consultar.chamadas) == 4


def test_orcamento_zero_nao_consulta():
    G = grafo_quatro_pontos()
    preparar(G, consultar_de(G, {}, padrao=(50.0, 40.0)))
    indice = indexar(G)
    consultar = consultar_de(G, {}, padrao=(50.0, 40.0))
    r = atualizar_transito(G, indice, consultar, orcamento=0)
    assert consultar.chamadas == [] and r.consultados == 0 and r.pulados_por_orcamento == 4
    assert r.alteradas == frozenset()


def test_reescreve_so_as_arestas_do_ponto_que_mudou():
    G = grafo_reta()
    preparar(G, consultar_de(G, {}, padrao=(50.0, 40.0)))
    indice = indexar(G)
    antes = instantaneo(G)
    ponto_ab = ponto_medio(G, "A", "B", 0)

    def consultar(lat, lon):
        return fluxo(50.0, 20.0) if (lat, lon) == ponto_ab else fluxo(50.0, 40.0)

    r = atualizar_transito(G, indice, consultar, agora=lambda: 5.0)
    assert r.alteradas == {("A", "B", 0), ("A", "B", 1)}  # as duas paralelas do ponto
    for a in r.alteradas:
        d = G.edges[a]
        assert d["v_atual"] == 20.0 and d["v_livre"] == 50.0
        assert d["t_atual"] == pytest.approx(d["length"] / (20.0 / 3.6))
        assert d["t_livre"] == pytest.approx(d["length"] / (50.0 / 3.6))
        assert d["litros"] != antes[a]["litros"]
    # todas as outras, inclusive a residential de mesma geometria: intactas, atributo a atributo
    for a, dados_antes in antes.items():
        if a not in r.alteradas:
            assert dict(G.edges[a]) == dados_antes
    # os atributos não variáveis das alteradas também continuam
    for a in r.alteradas:
        assert G.edges[a]["length"] == antes[a]["length"] and G.edges[a]["highway"] == "primary"


def test_diferenca_abaixo_da_tolerancia_nao_reescreve():
    G = grafo_quatro_pontos()
    preparar(G, consultar_de(G, {}, padrao=(50.0, 40.0)))
    indice = indexar(G)
    antes = instantaneo(G)
    r = atualizar_transito(G, indice, consultar_de(G, {}, padrao=(50.4, 40.9)),
                           tolerancia_kmh=1.0, agora=lambda: 9.0)
    assert r.alteradas == frozenset() and r.pioraram == frozenset() and r.melhoraram == frozenset()
    assert instantaneo(G) == antes
    assert r.consultados == 4 and r.falhas == 0
    # consulta bem-sucedida: ultima avança mesmo sem alterar a aresta
    assert all(t == 9.0 for t in indice.ultima.values())


def test_diferenca_igual_a_tolerancia_reescreve():
    G = grafo_quatro_pontos()
    preparar(G, consultar_de(G, {}, padrao=(50.0, 40.0)))
    indice = indexar(G)
    r = atualizar_transito(G, indice, consultar_de(G, {}, padrao=(50.0, 41.0)), tolerancia_kmh=1.0)
    assert len(r.alteradas) == 4
    assert all(G.edges[a]["v_atual"] == 41.0 for a in r.alteradas)


def test_so_v_livre_mudando_tambem_conta():
    G = grafo_quatro_pontos()
    preparar(G, consultar_de(G, {}, padrao=(50.0, 40.0)))
    indice = indexar(G)
    r = atualizar_transito(G, indice, consultar_de(G, {}, padrao=(60.0, 40.0)))
    assert len(r.alteradas) == 4
    assert all(G.edges[a]["t_livre"] < r.anteriores[a]["t_livre"] for a in r.alteradas)
    assert r.pioraram == frozenset() and r.melhoraram == frozenset()  # t_atual igual


def test_pioraram_e_melhoraram_pela_variacao_de_t_atual():
    G = grafo_quatro_pontos()
    preparar(G, consultar_de(G, {}, padrao=(50.0, 40.0)))
    indice = indexar(G)
    novo = {(0, 1, 0): (50.0, 10.0), (1, 2, 0): (50.0, 49.0), (2, 3, 0): (50.0, 40.0), (3, 4, 0): (50.0, 25.0)}
    r = atualizar_transito(G, indice, consultar_de(G, novo))
    assert r.pioraram == {(0, 1, 0), (3, 4, 0)}
    assert r.melhoraram == {(1, 2, 0)}
    assert r.alteradas == {(0, 1, 0), (1, 2, 0), (3, 4, 0)}  # (2,3,0) sem mudança
    assert r.pioraram | r.melhoraram == r.alteradas


def test_anteriores_guarda_valores_antigos():
    G = grafo_quatro_pontos()
    preparar(G, consultar_de(G, {}, padrao=(50.0, 40.0)))
    indice = indexar(G)
    antes = instantaneo(G)
    r = atualizar_transito(G, indice, consultar_de(G, {(0, 1, 0): (60.0, 15.0)}, padrao=(50.0, 40.0)))
    assert set(r.anteriores) == r.alteradas == {(0, 1, 0)}
    ant = r.anteriores[(0, 1, 0)]
    for peso in PESOS_ATUALIZAVEIS:
        assert ant[peso] == antes[(0, 1, 0)][peso]
        assert G.edges[0, 1, 0][peso] != ant[peso]


def test_falha_mantem_valor_antigo_nao_avanca_ultima_e_nao_derruba():
    G = grafo_quatro_pontos()
    preparar(G, consultar_de(G, {}, padrao=(50.0, 40.0)))
    indice = indexar(G)
    ruim = ponto_medio(G, 1, 2, 0)
    antes = instantaneo(G)

    def consultar(lat, lon):
        if (lat, lon) == ruim:
            raise TimeoutError("sem rede")
        return fluxo(50.0, 10.0)

    r = atualizar_transito(G, indice, consultar, agora=lambda: 42.0)
    assert r.falhas == 1 and r.consultados == 4
    assert dict(G.edges[1, 2, 0]) == antes[(1, 2, 0)]            # valor antigo mantido
    assert (1, 2, 0) not in r.alteradas
    assert indice.ultima[ruim] == 0.0                               # não avançou
    assert all(t == 42.0 for p, t in indice.ultima.items() if p != ruim)
    assert r.alteradas == {(0, 1, 0), (2, 3, 0), (3, 4, 0)}        # o laço seguiu

    # no próximo ciclo o ponto com falha volta ao topo da fila
    consultar2 = consultar_de(G, {}, padrao=(50.0, 10.0))
    atualizar_transito(G, indice, consultar2, orcamento=1, agora=lambda: 43.0)
    assert consultar2.chamadas == [ruim]
    assert indice.ultima[ruim] == 43.0


@pytest.mark.parametrize("resposta", [
    {},
    {"freeFlowSpeed": 50.0},
    {"currentSpeed": 30.0},
    {"currentSpeed": 0, "freeFlowSpeed": 50.0},
    {"currentSpeed": -5, "freeFlowSpeed": 50.0},
    {"currentSpeed": 30.0, "freeFlowSpeed": 0},
    {"currentSpeed": "abc", "freeFlowSpeed": 50.0},
    None,
])
def test_resposta_incompleta_ou_invalida_conta_como_falha(resposta):
    G = grafo_quatro_pontos()
    preparar(G, consultar_de(G, {}, padrao=(50.0, 40.0)))
    indice = indexar(G)
    antes = instantaneo(G)
    r = atualizar_transito(G, indice, lambda lat, lon: resposta, agora=lambda: 3.0)
    assert r.falhas == 4 and r.consultados == 4
    assert r.alteradas == frozenset()
    assert instantaneo(G) == antes
    assert all(t == 0 for t in indice.ultima.values())


def test_agora_injetado_define_ultima():
    G = grafo_quatro_pontos()
    preparar(G, consultar_de(G, {}, padrao=(50.0, 40.0)))
    indice = indexar(G)
    atualizar_transito(G, indice, consultar_de(G, {}, padrao=(50.0, 40.0)), orcamento=2, agora=lambda: 123.5)
    valores = sorted(indice.ultima.values())
    assert valores == [0.0, 0.0, 123.5, 123.5]


def test_g_nao_ganha_nem_perde_nos_ou_arestas():
    G = grafo_reta()
    preparar(G, consultar_de(G, {}, padrao=(50.0, 40.0)))
    indice = indexar(G)
    nos, arestas = set(G.nodes), set(G.edges(keys=True))
    atualizar_transito(G, indice, consultar_de(G, {}, padrao=(80.0, 10.0)))
    assert set(G.nodes) == nos and set(G.edges(keys=True)) == arestas
    # o índice também não muda de estrutura
    assert indice.arestas_por_ponto == indexar(G).arestas_por_ponto


def test_segunda_chamada_sem_mudanca_nao_altera_nada():
    G = grafo_reta()
    preparar(G, consultar_de(G, {}, padrao=(50.0, 40.0)))
    indice = indexar(G)
    consultar = consultar_de(G, {}, padrao=(80.0, 10.0))
    r1 = atualizar_transito(G, indice, consultar, agora=lambda: 1.0)
    assert r1.alteradas
    estado = instantaneo(G)
    r2 = atualizar_transito(G, indice, consultar, agora=lambda: 2.0)
    assert r2.alteradas == frozenset() and r2.pioraram == frozenset() and r2.melhoraram == frozenset()
    assert r2.anteriores == {}
    assert instantaneo(G) == estado


def test_aresta_sem_velocidades_previas_e_alterada():
    G = grafo_quatro_pontos()  # sem atribuir_pesos: nenhuma aresta tem v_livre/v_atual
    indice = indexar(G)
    r = atualizar_transito(G, indice, consultar_de(G, {}, padrao=(50.0, 40.0)))
    assert len(r.alteradas) == 4
    for a in r.alteradas:
        assert G.edges[a]["t_atual"] == pytest.approx(G.edges[a]["length"] / (40.0 / 3.6))
        assert G.edges[a]["litros"] > 0


def test_arestas_com_length_ausente_nao_quebram():
    G = grafo_quatro_pontos()
    del G.edges[0, 1, 0]["length"]
    preparar(G, consultar_de(G, {}, padrao=(50.0, 40.0)))
    indice = indexar(G)
    r = atualizar_transito(G, indice, consultar_de(G, {}, padrao=(50.0, 20.0)))
    assert G.edges[0, 1, 0]["t_atual"] == math.inf and G.edges[0, 1, 0]["litros"] == math.inf
    assert (0, 1, 0) in r.alteradas
    assert (0, 1, 0) not in r.pioraram and (0, 1, 0) not in r.melhoraram  # inf == inf


def test_incremental_igual_ao_completo():
    resposta = (65.0, 12.5)
    G = grafo_reta()
    preparar(G, consultar_de(G, {}, padrao=(50.0, 40.0)))
    indice = indexar(G)
    r = atualizar_transito(G, indice, consultar_de(G, {}, padrao=resposta))
    assert r.alteradas

    G2 = grafo_reta()
    atribuir_pesos(G2, consultar_de(G2, {}, padrao=resposta))
    atribuir_consumo(G2)
    for a in r.alteradas:
        for atributo in ("v_livre", "v_atual", "t_livre", "t_atual", "litros"):
            assert G.edges[a][atributo] == G2.edges[a][atributo], (a, atributo)


def test_incremental_igual_ao_completo_com_veiculo_customizado():
    from dataclasses import replace

    veiculo = replace(PADRAO, nome="beberrao", a=5.0)
    G = grafo_quatro_pontos()
    preparar(G, consultar_de(G, {}, padrao=(50.0, 40.0)))
    indice = indexar(G)
    r = atualizar_transito(G, indice, consultar_de(G, {}, padrao=(50.0, 15.0)), veiculo=veiculo)

    G2 = grafo_quatro_pontos()
    atribuir_pesos(G2, consultar_de(G2, {}, padrao=(50.0, 15.0)))
    atribuir_consumo(G2, veiculo)
    for a in r.alteradas:
        assert G.edges[a]["litros"] == G2.edges[a]["litros"]


# ---------- rota_continua_otima: casos dirigidos ----------

def grafo_losango(comp_rota=1000.0, comp_alt=1000.0):
    """A -> B -> D (rota) e A -> C -> D (alternativa), todas TomTom (primary)."""
    G = nx.MultiDiGraph()
    for no, (x, y) in {"A": (0.0, 0.0), "B": (0.01, 0.01), "C": (0.01, -0.01), "D": (0.02, 0.0)}.items():
        G.add_node(no, x=x, y=y)
    G.add_edge("A", "B", length=comp_rota, highway="primary")
    G.add_edge("B", "D", length=comp_rota, highway="primary")
    G.add_edge("A", "C", length=comp_alt, highway="primary")
    G.add_edge("C", "D", length=comp_alt, highway="primary")
    return G


ROTA = [("A", "B", 0), ("B", "D", 0)]


def montar_losango(vel_rota, vel_alt, **kw):
    """vel_*: v_atual (km/h) das arestas da rota e da alternativa; v_livre fixo em 130."""
    G = grafo_losango(**kw)
    inicial = {("A", "B", 0): (130.0, vel_rota), ("B", "D", 0): (130.0, vel_rota),
               ("A", "C", 0): (130.0, vel_alt[0]), ("C", "D", 0): (130.0, vel_alt[1])}
    preparar(G, consultar_de(G, inicial))
    return G, indexar(G), inicial


def atualizar_e_checar(G, indice, inicial, mudancas, peso):
    rota = menor_rota(G, "A", "D", peso)
    assert rota.arestas == ROTA  # premissa do cenário
    novo = {**inicial, **{a: (130.0, v) for a, v in mudancas.items()}}
    r = atualizar_transito(G, indice, consultar_de(G, novo))
    veredito = rota_continua_otima(G, rota, r, peso)
    if veredito:  # nunca um True errado
        custo_rota = sum(G.edges[a][peso] for a in rota.arestas)
        assert menor_rota(G, "A", "D", peso).custo == pytest.approx(custo_rota)
    return veredito, r


@pytest.mark.parametrize("peso", ["t_atual", "t_livre", "litros", "length"])
def test_nada_mudou_continua_otima(peso):
    G, indice, inicial = montar_losango(65.0, (30.0, 30.0), comp_rota=900.0)
    veredito, r = atualizar_e_checar(G, indice, inicial, {}, peso)
    assert r.alteradas == frozenset()
    assert veredito is True


@pytest.mark.parametrize("peso", ["t_atual", "litros"])
def test_aresta_da_rota_mudou_nao_e_otima(peso):
    G, indice, inicial = montar_losango(65.0, (30.0, 30.0), comp_rota=900.0)
    veredito, r = atualizar_e_checar(G, indice, inicial, {("B", "D", 0): 20.0}, peso)
    assert ("B", "D", 0) in r.alteradas
    assert veredito is False


def test_aresta_da_rota_melhorou_tambem_da_false():
    G, indice, inicial = montar_losango(40.0, (30.0, 30.0), comp_rota=900.0)
    veredito, _ = atualizar_e_checar(G, indice, inicial, {("A", "B", 0): 65.0}, "t_atual")
    assert veredito is False  # a rota segue ótima de fato, mas o teste é conservador


@pytest.mark.parametrize("peso", ["t_atual", "litros"])
def test_so_piorou_fora_da_rota_continua_otima(peso):
    G, indice, inicial = montar_losango(65.0, (65.0, 65.0), comp_rota=900.0)
    # alternativa: 65 -> 25 em uma aresta (t sobe e litros sobem: 65 e o minimo de consumo)
    veredito, r = atualizar_e_checar(G, indice, inicial, {("A", "C", 0): 25.0}, peso)
    assert r.alteradas == {("A", "C", 0)} and r.pioraram == r.alteradas
    assert veredito is True


@pytest.mark.parametrize("peso", ["t_atual", "litros"])
def test_algo_melhorou_fora_da_rota_da_false(peso):
    G, indice, inicial = montar_losango(65.0, (20.0, 65.0), comp_rota=1000.0)
    veredito, r = atualizar_e_checar(G, indice, inicial, {("A", "C", 0): 65.0}, peso)
    assert r.melhoraram == {("A", "C", 0)}
    assert veredito is False


def test_length_sempre_true():
    G, indice, inicial = montar_losango(65.0, (20.0, 65.0))
    rota = menor_rota(G, "A", "D", "length")
    r = atualizar_transito(G, indice, consultar_de(G, {}, padrao=(130.0, 5.0)))
    assert r.alteradas
    assert rota_continua_otima(G, rota, r, "length") is True
    # mesmo alterando arestas da propria rota
    assert set(rota.arestas) & r.alteradas
    assert rota_continua_otima(G, rota, r, "length") is True


def test_litros_velocidade_sobe_de_20_para_65_fora_da_rota():
    G, indice, inicial = montar_losango(65.0, (20.0, 65.0))
    rota = menor_rota(G, "A", "D", "litros")
    assert rota.arestas == ROTA
    novo = {**inicial, ("A", "C", 0): (130.0, 65.0)}
    r = atualizar_transito(G, indice, consultar_de(G, novo))
    ant = r.anteriores[("A", "C", 0)]
    assert G.edges["A", "C", 0]["litros"] < ant["litros"]   # consumo cai
    assert G.edges["A", "C", 0]["t_atual"] < ant["t_atual"]  # t_atual tambem cai
    assert rota_continua_otima(G, rota, r, "litros") is False
    assert rota_continua_otima(G, rota, r, "t_atual") is False


def test_litros_sobe_embora_t_atual_caia_usa_o_proprio_peso():
    # rota mais curta (900 m) a 65 km/h; alternativa de 1000 m a 65 km/h
    G, indice, inicial = montar_losango(65.0, (65.0, 65.0), comp_rota=900.0)
    rota_l = menor_rota(G, "A", "D", "litros")
    rota_t = menor_rota(G, "A", "D", "t_atual")
    assert rota_l.arestas == ROTA and rota_t.arestas == ROTA
    novo = {**inicial, ("A", "C", 0): (130.0, 120.0)}  # 65 -> 120: t_atual cai, litros sobe
    r = atualizar_transito(G, indice, consultar_de(G, novo))
    d = G.edges["A", "C", 0]
    ant = r.anteriores[("A", "C", 0)]
    assert d["t_atual"] < ant["t_atual"] and d["litros"] > ant["litros"]
    assert ("A", "C", 0) in r.melhoraram
    # litros: a aresta so ficou pior, rota continua otima de fato
    assert rota_continua_otima(G, rota_l, r, "litros") is True
    assert menor_rota(G, "A", "D", "litros").custo == pytest.approx(rota_l.custo)
    # t_atual: surgiu atalho (aresta 1000 m a 120 km/h) -> False, e de fato a rota mudou
    assert rota_continua_otima(G, rota_t, r, "t_atual") is False
    assert menor_rota(G, "A", "D", "t_atual").arestas != rota_t.arestas


def test_litros_cai_embora_t_atual_suba_usa_o_proprio_peso():
    G, indice, inicial = montar_losango(65.0, (120.0, 65.0), comp_rota=900.0, comp_alt=3000.0)
    rota = menor_rota(G, "A", "D", "t_atual")
    rota_l = menor_rota(G, "A", "D", "litros")
    assert rota.arestas == ROTA and rota_l.arestas == ROTA
    novo = {**inicial, ("A", "C", 0): (130.0, 65.0)}  # 120 -> 65: t_atual sobe, litros cai
    r = atualizar_transito(G, indice, consultar_de(G, novo))
    assert ("A", "C", 0) in r.pioraram
    assert rota_continua_otima(G, rota, r, "t_atual") is True
    assert rota_continua_otima(G, rota_l, r, "litros") is False


def test_peso_nao_controlado_pela_atualizacao_da_false_se_algo_mudou():
    G, indice, inicial = montar_losango(65.0, (30.0, 30.0), comp_rota=900.0)
    rota = menor_rota(G, "A", "D", "t_atual")
    r = atualizar_transito(G, indice, consultar_de(G, {**inicial, ("A", "C", 0): (130.0, 20.0)}))
    assert r.alteradas
    for a in G.edges(keys=True):
        G.edges[a]["custom"] = 1.0
    assert rota_continua_otima(G, rota, r, "custom") is False


# ---------- rota_continua_otima: propriedade em grafos aleatorios ----------

def grafo_aleatorio(rng):
    n = rng.randint(5, 8)
    G = nx.MultiDiGraph()
    for i in range(n):
        G.add_node(i, x=rng.uniform(-46.7, -46.6), y=rng.uniform(-23.6, -23.5))
    tipos = ["primary", "secondary", "tertiary", "trunk", "residential", "residential", "primary_link"]

    def aresta(u, v):
        G.add_edge(u, v, length=rng.uniform(50, 2000), highway=rng.choice(tipos))

    for i in range(n):  # anel: garante alcancabilidade
        aresta(i, (i + 1) % n)
    for _ in range(rng.randint(n, 3 * n)):
        u, v = rng.sample(range(n), 2)
        aresta(u, v)
        if rng.random() < 0.3:  # aresta paralela
            aresta(u, v)
    return G


def sortear_velocidades(G, rng):
    """{ponto medio: (livre, atual)} para cada ponto TomTom."""
    from tonton.ruas import eh_tomtom

    pontos = {}
    for u, v, k, d in G.edges(keys=True, data=True):
        if eh_tomtom(d):
            p = ponto_medio(G, u, v, k)
            if p not in pontos:
                livre = rng.uniform(30, 100)
                pontos[p] = (livre, rng.uniform(5, livre))
    return pontos


def mudar_transito(pontos, rng, cenario):
    novos = {}
    for p, (livre, atual) in pontos.items():
        if rng.random() < 0.4:
            if cenario == "piora":
                atual = atual * rng.uniform(0.3, 0.7)
            elif cenario == "melhora":
                atual = atual * rng.uniform(1.4, 2.5)
            else:  # mistura
                atual = atual * rng.choice([rng.uniform(0.3, 0.7), rng.uniform(1.4, 2.5)])
        novos[p] = (livre, atual)
    return novos


def consultar_por_ponto(pontos):
    def consultar(lat, lon):
        livre, atual = pontos[(lat, lon)]
        return fluxo(livre, atual)
    return consultar


def test_propriedade_true_nunca_e_errado():
    contagem = {"True": 0, "False": 0}
    por_peso = {}
    cenarios = ("piora", "melhora", "mistura")
    for seed in range(200):
        rng = random.Random(seed)
        G = grafo_aleatorio(rng)
        antes = sortear_velocidades(G, rng)
        preparar(G, consultar_por_ponto(antes))
        indice = indexar(G)
        origem, destino = rng.sample(sorted(G.nodes), 2)
        rotas = {p: menor_rota(G, origem, destino, p) for p in ("t_atual", "t_livre", "litros")}

        depois = mudar_transito(antes, rng, cenarios[seed % 3])
        r = atualizar_transito(G, indice, consultar_por_ponto(depois))

        for peso, rota in rotas.items():
            veredito = rota_continua_otima(G, rota, r, peso)
            chave = (peso, veredito)
            por_peso[chave] = por_peso.get(chave, 0) + 1
            contagem[str(veredito)] += 1
            if veredito:
                custo_antigo_recalculado = sum(G.edges[a][peso] for a in rota.arestas)
                otimo = menor_rota(G, origem, destino, peso).custo
                assert otimo == pytest.approx(custo_antigo_recalculado, rel=1e-9, abs=1e-12), (
                    f"True errado: seed={seed} peso={peso} otimo={otimo} rota_antiga={custo_antigo_recalculado}"
                )
    print(f"\npropriedade: True={contagem['True']} False={contagem['False']} por peso={sorted(por_peso.items())}")
    assert contagem["True"] >= 30, "teste vazio: poucos Trues"
    assert contagem["False"] >= 30, "teste fraco: poucos Falses"


def test_propriedade_false_nem_sempre_e_necessario_mas_true_cobre_cenario_de_piora():
    """No cenário só de piora, a rota nunca fica pior que as demais por causa de arestas de fora:
    todo False vem de aresta da própria rota ter sido alterada (para t_atual)."""
    trues = 0
    for seed in range(200):
        rng = random.Random(1000 + seed)
        G = grafo_aleatorio(rng)
        antes = sortear_velocidades(G, rng)
        preparar(G, consultar_por_ponto(antes))
        indice = indexar(G)
        origem, destino = rng.sample(sorted(G.nodes), 2)
        rota = menor_rota(G, origem, destino, "t_atual")
        r = atualizar_transito(G, indice, consultar_por_ponto(mudar_transito(antes, rng, "piora")))
        veredito = rota_continua_otima(G, rota, r, "t_atual")
        assert veredito == (not (set(rota.arestas) & r.alteradas))
        trues += veredito
    assert trues > 0
