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
             ignorar_vertices=frozenset(), ignorar_arestas=frozenset()):
    """Menor peso da origem a todos os vértices (ou até o destino, se informado).

    Devolve (dist, pred); pred[v] = (u, chave). Exige peso >= 0.
    `ignorar_vertices` e `ignorar_arestas` ((u, v, chave)) são filtrados dentro do laço,
    sem alterar G: usados pelo algoritmo de Yen (menores_rotas).
    """
    if origem not in G:
        raise RotaInexistente(f"origem {origem} não está no grafo")
    if G.number_of_edges() and not any(peso in d for _, _, d in G.edges(data=True)):
        raise KeyError(f"nenhuma aresta tem o atributo de peso '{peso}'")
    dist = {origem: 0.0}
    pred = {}
    pronto = set()
    fila = [(0.0, 0, origem)]  # (distância, desempate, vértice)
    n = 0
    while fila:
        d, _, u = heapq.heappop(fila)
        if d > dist[u]:  # entrada obsoleta
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
                heapq.heappush(fila, (dist[v], n, v))
    return dist, pred


def menor_rota(G, origem, destino, peso: str = "t_atual", *,
               ignorar_vertices=frozenset(), ignorar_arestas=frozenset()) -> Rota:
    """Rota de menor peso entre origem e destino (custo na unidade do peso).

    `ignorar_vertices` / `ignorar_arestas` excluem partes do grafo só nesta busca (G não muda).
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
                          ignorar_arestas=ignorar_arestas)
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


def _yen(G, origem, destino, peso):
    """Gera, em custo crescente, os caminhos SEM LAÇOS de origem a destino (algoritmo de Yen).

    Gerador preguiçoso: quem consome decide quantos pedir. Identidade do caminho = sequência
    de vértices; em multigrafo vale a aresta paralela de menor peso (como em menor_rota).
    Empate de custo: ordem de descoberta (contador), logo determinística.
    """
    primeira = menor_rota(G, origem, destino, peso)  # levanta RotaInexistente se não houver
    aceitas = [primeira]
    yield primeira
    if origem == destino:
        return
    vistos = {tuple(primeira.vertices)}
    candidatas = []  # heap (custo, contador, Rota)
    contador = itertools.count()
    while True:
        anterior = aceitas[-1]
        custo_raiz = 0.0
        for i in range(len(anterior.vertices) - 1):
            desvio = anterior.vertices[i]
            raiz = anterior.vertices[:i + 1]
            if i > 0:
                u, v, chave = anterior.arestas[i - 1]
                custo_raiz += G[u][v][chave][peso]
            # proíbe sair do desvio pelos trechos que as rotas aceitas com a mesma raiz já usaram
            proibidas = set()
            for r in aceitas:
                if r.vertices[:i + 1] == raiz and len(r.vertices) > i + 1:
                    a, b = r.vertices[i], r.vertices[i + 1]
                    proibidas.update((a, b, chave) for chave in G[a][b])  # todas as paralelas
            try:
                trecho = menor_rota(G, desvio, destino, peso, ignorar_vertices=frozenset(raiz[:-1]),
                                    ignorar_arestas=frozenset(proibidas))
            except RotaInexistente:
                continue
            vertices = raiz[:-1] + trecho.vertices
            if tuple(vertices) in vistos:
                continue
            vistos.add(tuple(vertices))
            rota = Rota(vertices, anterior.arestas[:i] + trecho.arestas, custo_raiz + trecho.custo, peso)
            heapq.heappush(candidatas, (rota.custo, next(contador), rota))
        if not candidatas:
            return
        proxima = heapq.heappop(candidatas)[2]
        aceitas.append(proxima)
        yield proxima


def menores_rotas(G, origem, destino, k: int = 3, peso: str = "t_atual") -> list:
    """As k rotas de menor peso SEM LAÇOS (Yen), em custo crescente; menos de k se não houver k.

    origem == destino: [rota vazia]. Destino inalcançável: RotaInexistente.
    """
    if k < 1:
        raise ValueError(f"k deve ser >= 1: {k}")
    return list(itertools.islice(_yen(G, origem, destino, peso), k))


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
                       max_sobreposicao: float = 0.8, max_candidatos: int = 50) -> list:
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
    for candidata in itertools.islice(_yen(G, origem, destino, peso), max_candidatos):
        if aceitas and _sobreposicao(G, candidata, arestas_aceitas) > max_sobreposicao:
            continue
        aceitas.append(candidata)
        arestas_aceitas.append(set(candidata.arestas))
        if len(aceitas) == k:
            break
    return aceitas
