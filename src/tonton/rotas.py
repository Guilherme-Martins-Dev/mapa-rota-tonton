"""Etapa 3: Dijkstra escrito à mão (heapq) para a rota de menor peso.

O peso é o nome do atributo da aresta: t_atual / t_livre (segundos) ou length (metros).
O custo da Rota está na unidade do peso escolhido.
"""
import heapq
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


def menor_peso_aresta(G, u, v, peso: str):
    """Entre as arestas paralelas u->v, devolve (chave, peso) da de menor peso.

    Peso ausente, None, nan ou inf conta como aresta inexistente (devolve (None, inf) se
    nenhuma serve). Empate: menor chave. Peso negativo: ValueError.
    """
    melhor_chave, melhor = None, math.inf
    for chave, dados in G[u][v].items():
        w = dados.get(peso)
        if w is None or math.isnan(w) or math.isinf(w):
            continue
        if w < 0:
            raise ValueError(f"peso '{peso}' negativo na aresta ({u}, {v}, {chave}): {w}")
        if w < melhor or (w == melhor and chave < melhor_chave):
            melhor_chave, melhor = chave, w
    return melhor_chave, melhor


def dijkstra(G, origem, peso: str = "t_atual", destino=None):
    """Menor peso da origem a todos os vértices (ou até o destino, se informado).

    Devolve (dist, pred); pred[v] = (u, chave). Exige peso >= 0.
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
            chave, w = menor_peso_aresta(G, u, v, peso)
            if chave is None:
                continue
            # relaxamento
            if dist[u] + w < dist.get(v, math.inf):
                dist[v] = dist[u] + w
                pred[v] = (u, chave)
                n += 1
                heapq.heappush(fila, (dist[v], n, v))
    return dist, pred


def menor_rota(G, origem, destino, peso: str = "t_atual") -> Rota:
    """Rota de menor peso entre origem e destino (custo na unidade do peso)."""
    if origem not in G:
        raise RotaInexistente(f"origem {origem} não está no grafo")
    if destino not in G:
        raise RotaInexistente(f"destino {destino} não está no grafo")
    if origem == destino:
        return Rota([origem], [], 0.0, peso)
    dist, pred = dijkstra(G, origem, peso, destino)
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
