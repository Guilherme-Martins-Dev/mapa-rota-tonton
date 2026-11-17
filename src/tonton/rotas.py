"""Etapa 3: Dijkstra escrito à mão (heapq) para a rota de menor peso.

O peso é o nome do atributo da aresta: t_atual / t_livre (segundos) ou length (metros).
O custo da Rota está na unidade do peso escolhido.
"""
import heapq
import itertools
import math
from dataclasses import dataclass


class RotaInexistente(ValueError):
    """Origem/destino fora do grafo ou destino inalcançável."""


@dataclass(frozen=True)
class Rota:
    vertices: list  # origem ... destino
    arestas: list   # (u, v, chave): a aresta paralela de menor peso em cada trecho
    custo: float    # soma do atributo de peso (segundos para t_*, metros para length)
    peso: str       # nome do atributo usado


_RAIO_TERRA_M = 6371009.0  # o mesmo raio que o osmnx usa para calcular `length`


def _haversine(lat1, lon1, lat2, lon2) -> float:
    """Distância em metros sobre a esfera (grande círculo) entre dois pontos em graus."""
    f1, f2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((f2 - f1) / 2) ** 2 + math.cos(f1) * math.cos(f2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * _RAIO_TERRA_M * math.asin(math.sqrt(a))


def heuristica_haversine(G, destino, peso: str):
    """Heurística do A*: h(v) = c × haversine(v, destino), ou None se não der para usá-la com segurança.

    c = r_min × escala, varrendo TODAS as arestas (O(E)) a cada chamada, sem guardar nada no grafo
    (assim continua válida depois de `atualizar_transito`, que pode aumentar velocidades):
      r_min  = min (peso / length) entre as arestas com length > 0 e peso finito;
      escala = min(1, min length / haversine(u, v)), para o caso de `length` menor que a distância das
               coordenadas (grafos sintéticos); no OSM real length >= haversine e a escala é 1.
    Aresta com length ausente ou <= 0 entra por peso / haversine(u, v). Resultado:
    para toda aresta, peso >= c × haversine(u, v); com a desigualdade triangular da haversine,
    h é ADMISSÍVEL (h(v) <= custo real de v ao destino) e CONSISTENTE (h(u) <= w(u, v) + h(v)).
    O c leva um fator 1 - 1e-9 contra erro de arredondamento. Devolve None (volta ao Dijkstra puro)
    se faltar x/y em algum vértice, houver peso negativo, não houver aresta útil ou c for 0.
    A função devolvida guarda os h(v) já calculados; vale só para este destino e este peso.
    """
    try:
        coord = {n: (float(d["y"]), float(d["x"])) for n, d in G.nodes(data=True)}
        y_dest, x_dest = coord[destino]
    except (KeyError, TypeError, ValueError):
        return None
    r_min, escala, direto = math.inf, 1.0, math.inf
    for u, v, dados in G.edges(data=True):
        w = dados.get(peso)
        if w is None or math.isnan(w) or math.isinf(w):
            continue
        if w < 0:
            return None  # o Dijkstra recusa peso negativo; sem heurística, ele mesmo avisa
        dist_reta = _haversine(*coord[u], *coord[v])
        comprimento = dados.get("length")
        if comprimento is not None and math.isfinite(comprimento) and comprimento > 0:
            r_min = min(r_min, w / comprimento)
            if dist_reta > 0:
                escala = min(escala, comprimento / dist_reta)
        elif dist_reta > 0:
            direto = min(direto, w / dist_reta)
    c = min(r_min * escala, direto) * (1 - 1e-9)
    if not 0 < c < math.inf:
        return None
    memo = {}

    def h(v):
        if v not in memo:
            memo[v] = c * _haversine(*coord[v], y_dest, x_dest)
        return memo[v]
    return h


def menor_peso_aresta(G, u, v, peso: str, *, ignorar_arestas=frozenset()):
    """Entre as arestas paralelas u->v, devolve (chave, peso) da de menor peso.

    Peso ausente, None, nan ou inf conta como aresta inexistente (devolve (None, inf) se
    nenhuma serve). Empate: menor chave. Peso negativo: ValueError.
    Arestas (u, v, chave) em `ignorar_arestas` são puladas, como se não existissem.
    """
    melhor_chave, melhor = None, math.inf
    for chave, dados in G[u][v].items():
        if (u, v, chave) in ignorar_arestas:
            continue
        w = dados.get(peso)
        if w is None or math.isnan(w) or math.isinf(w):
            continue
        if w < 0:
            raise ValueError(f"peso '{peso}' negativo na aresta ({u}, {v}, {chave}): {w}")
        if w < melhor or (w == melhor and chave < melhor_chave):
            melhor_chave, melhor = chave, w
    return melhor_chave, melhor


def dijkstra(G, origem, peso: str = "t_atual", destino=None, *,
             ignorar_vertices=frozenset(), ignorar_arestas=frozenset(), heuristica=None):
    """Menor peso da origem a todos os vértices (ou até o destino, se informado).

    Devolve (dist, pred); pred[v] = (u, chave). Exige peso >= 0.
    `ignorar_vertices` e `ignorar_arestas` ((u, v, chave)) são filtrados dentro do laço,
    sem alterar G: usados pelo algoritmo de Yen (menores_rotas).

    `heuristica` (função v -> estimativa do custo de v ao `destino`) liga o A*: a fila passa a ordenar
    por dist + h. Só dá o caminho ótimo se h for ADMISSÍVEL (nunca maior que o custo real) e CONSISTENTE
    (h(u) <= w(u, v) + h(v)): a consistência é o que torna definitivo o fechamento de um vértice na
    primeira vez que sai da fila (`pronto`), sem reabri-lo. Exige `destino`. Com A*, `dist` dos vértices
    ainda não fechados pode não ser o mínimo; o do destino é. Sem heurística, é o Dijkstra de sempre.
    """
    if origem not in G:
        raise RotaInexistente(f"origem {origem} não está no grafo")
    # `G.number_of_edges()` soma os graus (O(V)) a cada chamada: o Yen chama isto centenas de vezes
    dados_arestas = (d for _, _, d in G.edges(data=True))
    primeira = next(dados_arestas, None)
    if primeira is not None and peso not in primeira and not any(peso in d for d in dados_arestas):
        raise KeyError(f"nenhuma aresta tem o atributo de peso '{peso}'")
    dist = {origem: 0.0}
    pred = {}
    pronto = set()
    if heuristica is not None and destino is None:
        raise ValueError("heuristica exige destino")
    fila = [(0.0, 0, origem)]  # (prioridade = distância [+ h], desempate, vértice)
    n = 0
    while fila:
        d, _, u = heapq.heappop(fila)
        if heuristica is None and d > dist[u]:  # entrada obsoleta (com A*, `pronto` já basta)
            continue
        if u in pronto:
            continue
        pronto.add(u)
        if u == destino:
            break
        for v in G.successors(u):
            if v in ignorar_vertices:
                continue
            chave, w = menor_peso_aresta(G, u, v, peso, ignorar_arestas=ignorar_arestas)
            if chave is None:
                continue
            # relaxamento
            if dist[u] + w < dist.get(v, math.inf):
                dist[v] = dist[u] + w
                pred[v] = (u, chave)
                n += 1
                prioridade = dist[v] if heuristica is None else dist[v] + heuristica(v)
                heapq.heappush(fila, (prioridade, n, v))
    return dist, pred


def menor_rota(G, origem, destino, peso: str = "t_atual", *,
               ignorar_vertices=frozenset(), ignorar_arestas=frozenset(), heuristica=None) -> Rota:
    """Rota de menor peso entre origem e destino (custo na unidade do peso).

    `ignorar_vertices` / `ignorar_arestas` excluem partes do grafo só nesta busca (G não muda).
    `heuristica`: A*, ver `dijkstra`; `heuristica_haversine(G, destino, peso)` monta uma.
    """
    if origem not in G:
        raise RotaInexistente(f"origem {origem} não está no grafo")
    if destino not in G:
        raise RotaInexistente(f"destino {destino} não está no grafo")
    if origem == destino:
        return Rota([origem], [], 0.0, peso)
    if destino in ignorar_vertices:
        raise RotaInexistente(f"destino {destino} está em ignorar_vertices")
    dist, pred = dijkstra(G, origem, peso, destino, ignorar_vertices=ignorar_vertices,
                          ignorar_arestas=ignorar_arestas, heuristica=heuristica)
    if destino not in dist:
        raise RotaInexistente(f"não há caminho de {origem} até {destino} com peso '{peso}'")
    vertices, arestas = [destino], []
    v = destino
    while v != origem:
        u, chave = pred[v]
        arestas.append((u, v, chave))
        vertices.append(u)
        v = u
    vertices.reverse()
    arestas.reverse()
    return Rota(vertices, arestas, dist[destino], peso)


def _corte(candidatas, faltam: int) -> float:
    """Custo da `faltam`-ésima melhor candidata (inf se ainda não há tantas ou se a poda está desligada)."""
    if faltam < 1 or len(candidatas) < faltam:
        return math.inf
    return heapq.nsmallest(faltam, candidatas)[-1][0]


def _yen(G, origem, destino, peso, *, lawler=False, astar=False, poda_k=None):
    """Gera, em custo crescente, os caminhos SEM LAÇOS de origem a destino (algoritmo de Yen).

    Gerador preguiçoso: quem consome decide quantos pedir. Identidade do caminho = sequência
    de vértices; em multigrafo vale a aresta paralela de menor peso (como em menor_rota).
    Empate de custo: ordem de descoberta (contador), logo determinística.

    `lawler`: cada candidata guarda o índice do vértice onde se desviou da rota-pai; ao aceitá-la, só
    os desvios a partir desse índice são calculados (os anteriores têm a mesma raiz e as mesmas
    proibições, e já foram gerados pela rota-pai). `astar`: os desvios usam A* com a heurística
    haversine, calculada UMA vez (todos vão ao mesmo destino). Ambos devolvem os mesmos custos;
    com empate de custo a rota escolhida pode ser outra.
    `poda_k` (exige `astar`): sabendo que o consumidor só quer as `poda_k` melhores, pula o desvio cujo
    custo mínimo possível (custo da raiz + h(desvio)) já não entra entre as que faltam.
    """
    heuristica = heuristica_haversine(G, destino, peso) if astar and origem != destino else None
    primeira = menor_rota(G, origem, destino, peso, heuristica=heuristica)  # RotaInexistente se não houver
    aceitas = [primeira]
    yield primeira
    if origem == destino:
        return
    vistos = {tuple(primeira.vertices)}
    candidatas = []  # heap (custo, contador, Rota, índice do desvio)
    contador = itertools.count()
    inicio = 0  # primeiro índice de desvio a calcular para a rota recém-aceita
    while True:
        anterior = aceitas[-1]
        custo_raiz = 0.0
        faltam = poda_k - len(aceitas) if poda_k is not None and heuristica is not None else 0
        corte = _corte(candidatas, faltam)
        for i in range(len(anterior.vertices) - 1):
            desvio = anterior.vertices[i]
            raiz = anterior.vertices[:i + 1]
            if i > 0:
                u, v, chave = anterior.arestas[i - 1]
                custo_raiz += G[u][v][chave][peso]
            if i < inicio:
                continue
            if corte < math.inf and custo_raiz + heuristica(desvio) >= corte:
                continue  # nem o melhor desvio possível entraria nas k melhores
            # proíbe sair do desvio pelos trechos que as rotas aceitas com a mesma raiz já usaram
            proibidas = set()
            for r in aceitas:
                if r.vertices[:i + 1] == raiz and len(r.vertices) > i + 1:
                    a, b = r.vertices[i], r.vertices[i + 1]
                    proibidas.update((a, b, chave) for chave in G[a][b])  # todas as paralelas
            try:
                trecho = menor_rota(G, desvio, destino, peso, ignorar_vertices=frozenset(raiz[:-1]),
                                    ignorar_arestas=frozenset(proibidas), heuristica=heuristica)
            except RotaInexistente:
                continue
            vertices = raiz[:-1] + trecho.vertices
            if tuple(vertices) in vistos:
                continue
            vistos.add(tuple(vertices))
            rota = Rota(vertices, anterior.arestas[:i] + trecho.arestas, custo_raiz + trecho.custo, peso)
            heapq.heappush(candidatas, (rota.custo, next(contador), rota, i))
            corte = _corte(candidatas, faltam)
        if not candidatas:
            return
        _, _, proxima, indice = heapq.heappop(candidatas)
        inicio = indice if lawler else 0
        aceitas.append(proxima)
        yield proxima


def menores_rotas(G, origem, destino, k: int = 3, peso: str = "t_atual", *, otimizar: bool = True) -> list:
    """As k rotas de menor peso SEM LAÇOS (Yen), em custo crescente; menos de k se não houver k.

    origem == destino: [rota vazia]. Destino inalcançável: RotaInexistente.
    `otimizar=True` (padrão) liga Lawler e A* (ver `_yen`); `otimizar=False` é o Yen original.
    Os custos das k rotas são os mesmos nos dois modos (a rota pode diferir em empate de custo).
    """
    if k < 1:
        raise ValueError(f"k deve ser >= 1: {k}")
    return list(itertools.islice(_yen(G, origem, destino, peso, lawler=otimizar, astar=otimizar), k))


def _metros(G, aresta) -> float:
    u, v, chave = aresta
    comprimento = G[u][v][chave].get("length")
    return float(comprimento) if comprimento is not None and math.isfinite(comprimento) else 0.0


def _sobreposicao(G, candidata, arestas_aceitas) -> float:
    """Maior fração do comprimento da candidata que coincide com as arestas de UMA rota aceita."""
    total = sum(_metros(G, a) for a in candidata.arestas)
    if total == 0:
        return 0.0
    return max(sum(_metros(G, a) for a in candidata.arestas if a in usadas) for usadas in arestas_aceitas) / total


def rotas_alternativas(G, origem, destino, k: int = 3, peso: str = "t_atual",
                       max_sobreposicao: float = 0.8, max_candidatos: int = 50, *, otimizar: bool = True) -> list:
    """A melhor rota mais alternativas distintas (até k no total), em custo crescente.

    Pode devolver MENOS de k rotas, sem erro, se os candidatos acabarem ou `max_candidatos` for atingido.

    Os candidatos vêm de Yen (no máximo `max_candidatos`, contando a melhor). Um candidato só é
    aceito se a fração do seu comprimento (`length`, m; sem length conta 0) que usa arestas de
    UMA rota já aceita for <= max_sobreposicao. Yen puro devolve rotas que diferem num quarteirão.
    """
    if k < 1:
        raise ValueError(f"k deve ser >= 1: {k}")
    if not 0 <= max_sobreposicao <= 1:
        raise ValueError(f"max_sobreposicao deve estar em [0, 1]: {max_sobreposicao}")
    if max_candidatos < 1:
        raise ValueError(f"max_candidatos deve ser >= 1: {max_candidatos}")
    aceitas, arestas_aceitas = [], []
    for candidata in itertools.islice(_yen(G, origem, destino, peso, lawler=otimizar, astar=otimizar), max_candidatos):
        if aceitas and _sobreposicao(G, candidata, arestas_aceitas) > max_sobreposicao:
            continue
        aceitas.append(candidata)
        arestas_aceitas.append(set(candidata.arestas))
        if len(aceitas) == k:
            break
    return aceitas
