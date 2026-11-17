"""Etapa: otimização do Yen (Lawler + A*, decisão 005). Só grafos sintéticos, sem rede.

Cobre: `otimizar=True` (Lawler + A*) dá os mesmos custos que `otimizar=False` (Yen original);
`heuristica_haversine` é consistente (e os casos em que devolve None); A* com heurística dá o
mesmo dist[destino] que o Dijkstra puro; `_yen(lawler=True)` gera as mesmas rotas que
`lawler=False`; `poda_k` nunca omite uma rota que deveria estar entre as k melhores; chamadas
antigas (sem os novos kwargs) continuam funcionando; `planejador.planejar_alternativas` dá os
mesmos totais com `otimizar=True`/`False`.
"""
import itertools
import math
import random

import networkx as nx
import pytest

from tonton.planejador import Criterio, planejar_alternativas, preparar_grafo
from tonton.rotas import (
    RotaInexistente,
    _haversine,
    _yen,
    dijkstra,
    heuristica_haversine,
    menores_rotas,
)

_PESOS = ("length", "t_atual", "litros")
_KS = (1, 3, 5, 8)


def _grafo_coord(seed, n=7, m=18):
    """Grafo sintético com coordenadas, arestas paralelas e os 3 pesos do planejador.

    As coordenadas se espalham numa caixa maior do que os comprimentos sorteados, então
    `length` às vezes fica MENOR que a haversine(u, v): exercita a escala de segurança de
    `heuristica_haversine` (o caso que, no OSM real, nunca acontece).
    """
    rng = random.Random(seed)
    G = nx.MultiDiGraph()
    for i in range(n):
        G.add_node(i, y=-3.80 + rng.uniform(-0.01, 0.01), x=-38.50 + rng.uniform(-0.01, 0.01))
    for _ in range(m):
        u, v = rng.sample(range(n), 2)
        comprimento = float(rng.randint(1, 400))
        velocidade = rng.uniform(1.0, 20.0)  # m/s
        G.add_edge(u, v, length=comprimento, t_atual=comprimento / velocidade,
                   litros=comprimento * rng.uniform(0.05, 0.2))
    return G


def _grafo_ties(seed, n=5, m=22):
    """Grafo denso, sem coordenadas, com pesos inteiros pequenos: muitos empates e paralelas."""
    rng = random.Random(seed)
    G = nx.MultiDiGraph()
    G.add_nodes_from(range(n))
    for _ in range(m):
        u, v = rng.sample(range(n), 2)
        G.add_edge(u, v, t_atual=float(rng.randint(0, 3)), length=float(rng.randint(1, 4)))
    return G


# ---------- correção: otimizar=True dá os mesmos custos que otimizar=False ----------

@pytest.mark.parametrize("seed", range(160))
def test_otimizar_mesmos_custos_que_yen_original(seed):
    G = _grafo_coord(seed)
    rng = random.Random(seed + 1_000_000)
    origem, destino = rng.sample(range(G.number_of_nodes()), 2)
    for peso in _PESOS:
        for k in _KS:
            try:
                padrao = menores_rotas(G, origem, destino, k=k, peso=peso, otimizar=False)
            except RotaInexistente:
                with pytest.raises(RotaInexistente):
                    menores_rotas(G, origem, destino, k=k, peso=peso, otimizar=True)
                continue
            otim = menores_rotas(G, origem, destino, k=k, peso=peso, otimizar=True)
            assert len(otim) == len(padrao)
            assert [r.custo for r in otim] == pytest.approx([r.custo for r in padrao], abs=1e-9)


def test_otimizar_origem_igual_destino():
    for seed in range(10):
        G = _grafo_coord(seed)
        for peso in _PESOS:
            for k in (1, 3):
                com = menores_rotas(G, 2, 2, k=k, peso=peso, otimizar=True)
                sem = menores_rotas(G, 2, 2, k=k, peso=peso, otimizar=False)
                assert [r.custo for r in com] == [r.custo for r in sem] == [0.0]
                assert com[0].vertices == sem[0].vertices == [2]


def test_otimizar_destino_inalcancavel_mesmo_erro_nos_dois_modos():
    G = nx.MultiDiGraph()
    G.add_node(0, y=-3.80, x=-38.50)
    G.add_node(1, y=-3.81, x=-38.49)
    G.add_edge(0, 0, t_atual=1.0, length=1.0, litros=1.0)  # não leva a lugar nenhum além de si mesmo
    for peso in _PESOS:
        for otimizar in (True, False):
            with pytest.raises(RotaInexistente):
                menores_rotas(G, 0, 1, k=3, peso=peso, otimizar=otimizar)


# ---------- heuristica_haversine ----------

def test_heuristica_consistente_em_varias_arestas():
    checados = 0
    for seed in range(40):
        G = _grafo_coord(seed)
        for destino in range(G.number_of_nodes()):
            for peso in _PESOS:
                h = heuristica_haversine(G, destino, peso)
                if h is None:
                    continue
                assert h(destino) == 0.0
                for u, v, dados in G.edges(data=True):
                    w = dados.get(peso)
                    assert h(u) <= w + h(v) + 1e-9, (seed, destino, peso, u, v, w, h(u), h(v))
                    checados += 1
    assert checados > 500


def test_heuristica_fallback_por_haversine_sem_length():
    G = nx.MultiDiGraph()
    G.add_node("u", y=0.0, x=0.0)
    G.add_node("d", y=0.0, x=0.01)  # ~1113 m de "u"
    G.add_edge("u", "d", t_atual=100.0)  # sem length: cai no fallback peso / haversine(u, v)
    h = heuristica_haversine(G, "d", "t_atual")
    assert h is not None
    assert h("u") == pytest.approx(100.0 * (1 - 1e-9))
    assert h("d") == 0.0


@pytest.mark.parametrize("comprimento", [0.0, -5.0])
def test_heuristica_length_nao_positivo_cai_no_mesmo_fallback(comprimento):
    G = nx.MultiDiGraph()
    G.add_node("u", y=0.0, x=0.0)
    G.add_node("d", y=0.0, x=0.01)
    G.add_edge("u", "d", t_atual=50.0, length=comprimento)
    h = heuristica_haversine(G, "d", "t_atual")
    assert h is not None
    assert h("u") == pytest.approx(50.0 * (1 - 1e-9))


def test_heuristica_sem_nenhuma_aresta_devolve_none():
    G = nx.MultiDiGraph()
    G.add_node("a", y=0.0, x=0.0)
    G.add_node("d", y=0.0, x=0.01)
    assert heuristica_haversine(G, "d", "t_atual") is None


def test_heuristica_peso_ausente_em_todas_as_arestas_devolve_none():
    G = nx.MultiDiGraph()
    G.add_node("a", y=0.0, x=0.0)
    G.add_node("d", y=0.0, x=0.01)
    G.add_edge("a", "d", length=100.0)  # não tem 't_atual'
    assert heuristica_haversine(G, "d", "t_atual") is None


def test_heuristica_aresta_sem_length_e_mesma_coordenada_devolve_none():
    """dist_reta == 0 e sem length: a aresta não contribui com nada; sem outra, não há heurística."""
    G = nx.MultiDiGraph()
    G.add_node("a", y=0.0, x=0.0)
    G.add_node("d", y=0.0, x=0.0)
    G.add_edge("a", "d", t_atual=5.0)
    assert heuristica_haversine(G, "d", "t_atual") is None


def test_heuristica_peso_negativo_devolve_none():
    G = nx.MultiDiGraph()
    G.add_node("a", y=0.0, x=0.0)
    G.add_node("d", y=0.0, x=0.01)
    G.add_edge("a", "d", t_atual=-1.0, length=10.0)
    assert heuristica_haversine(G, "d", "t_atual") is None


def test_heuristica_destino_vale_zero_em_varios_grafos():
    testados = 0
    for seed in range(10):
        G = _grafo_coord(seed)
        for peso in _PESOS:
            h = heuristica_haversine(G, 3, peso)
            if h is not None:
                assert h(3) == 0.0
                testados += 1
    assert testados > 0


# ---------- A* dá o mesmo dist[destino] que o Dijkstra puro ----------

def test_astar_mesmo_dist_destino_que_dijkstra_puro():
    comparados = 0
    for seed in range(60):
        G = _grafo_coord(seed)
        for peso in _PESOS:
            for destino in (0, 3, 6):
                h = heuristica_haversine(G, destino, peso)
                for origem in range(G.number_of_nodes()):
                    if origem == destino:
                        continue
                    dist_puro, _ = dijkstra(G, origem, peso, destino)
                    dist_astar, _ = dijkstra(G, origem, peso, destino, heuristica=h)
                    if destino in dist_puro:
                        assert dist_astar[destino] == pytest.approx(dist_puro[destino], abs=1e-9)
                        comparados += 1
                    else:
                        assert destino not in dist_astar
    assert comparados > 200


# ---------- Lawler: mesma sequência de rotas que sem Lawler ----------

@pytest.mark.parametrize("seed", range(40))
def test_lawler_mesmas_rotas_que_sem_lawler(seed):
    G = _grafo_ties(seed)
    for peso in ("t_atual", "length"):
        for k in (1, 3, 5, 8, 20):
            try:
                com = list(itertools.islice(_yen(G, 0, 4, peso, lawler=True), k))
            except RotaInexistente:
                with pytest.raises(RotaInexistente):
                    list(itertools.islice(_yen(G, 0, 4, peso, lawler=False), k))
                continue
            sem = list(itertools.islice(_yen(G, 0, 4, peso, lawler=False), k))
            assert [(r.vertices, r.custo) for r in com] == [(r.vertices, r.custo) for r in sem]


# ---------- poda_k nunca omite uma rota que deveria entrar nas k melhores ----------

@pytest.mark.parametrize("seed", range(40))
def test_poda_k_nao_causa_falso_negativo(seed):
    G = _grafo_coord(seed)
    rng = random.Random(seed + 5_000)
    origem, destino = rng.sample(range(G.number_of_nodes()), 2)
    for peso in _PESOS:
        for k in _KS:
            try:
                sem_poda = list(itertools.islice(
                    _yen(G, origem, destino, peso, lawler=True, astar=True, poda_k=None), k))
            except RotaInexistente:
                with pytest.raises(RotaInexistente):
                    list(itertools.islice(
                        _yen(G, origem, destino, peso, lawler=True, astar=True, poda_k=k), k))
                continue
            com_poda = list(itertools.islice(
                _yen(G, origem, destino, peso, lawler=True, astar=True, poda_k=k), k))
            assert [r.custo for r in com_poda] == pytest.approx(
                [r.custo for r in sem_poda], abs=1e-9)


# ---------- compatibilidade: chamadas antigas continuam funcionando ----------

def test_compatibilidade_quadro_segunda_melhor_e_39():
    """Mesmo caso do quadro (ver test_rotas_alternativas), sem passar nenhum kwarg novo."""
    G = nx.MultiDiGraph()
    G.add_edge("s", "b", t_atual=4.0)
    G.add_edge("b", "v", t_atual=35.0)
    G.add_edge("s", "a", t_atual=6.0)
    G.add_edge("a", "v", t_atual=32.0)
    rotas = menores_rotas(G, "s", "v", k=3)
    assert [(r.vertices, r.custo) for r in rotas] == [(["s", "a", "v"], 38.0), (["s", "b", "v"], 39.0)]


def test_compatibilidade_dijkstra_sem_heuristica():
    G = nx.MultiDiGraph()
    G.add_edge("s", "a", t_atual=1.0)
    G.add_edge("a", "t", t_atual=1.0)
    dist, pred = dijkstra(G, "s")  # assinatura antiga: sem destino/heuristica
    assert dist == {"s": 0.0, "a": 1.0, "t": 2.0}
    assert pred == {"a": ("s", 0), "t": ("a", 0)}


def test_compatibilidade_mao_unica_nao_volta():
    G = nx.MultiDiGraph()
    G.add_edge("a", "b", t_atual=1.0)
    G.add_edge("b", "c", t_atual=1.0)
    assert len(menores_rotas(G, "a", "c", k=5)) == 1
    with pytest.raises(RotaInexistente):
        menores_rotas(G, "c", "a", k=5)


# ---------- planejador: otimizar=True/False dá os mesmos totais ----------

def _grafo_tres_vias():
    """s->t por 3 vias de velocidades diferentes (mesma estrutura de test_planejador)."""
    G = nx.MultiDiGraph()
    G.add_node("s", x=-38.500, y=-3.800)
    G.add_node("t", x=-38.460, y=-3.800)
    G.add_node("d", x=-38.480, y=-3.790)
    G.add_node("f", x=-38.480, y=-3.800)
    G.add_node("e", x=-38.480, y=-3.810)
    vias = {"d": (3000.0, "20"), "f": (5000.0, "120"), "e": (4000.0, "65")}
    for meio, (comp, ms) in vias.items():
        atributos = {"length": comp / 2, "maxspeed": ms}
        G.add_edge("s", meio, **atributos)
        G.add_edge(meio, "t", **atributos)
    G.add_edge("s", "d", length=5000.0, maxspeed="20")  # paralela pior, nunca escolhida
    return preparar_grafo(G)


@pytest.mark.parametrize("otimizar", [True, False])
def test_planejar_alternativas_otimizar_mesma_ordem_e_totais(otimizar):
    G = _grafo_tres_vias()
    rs = planejar_alternativas(G, "s", "t", Criterio.DISTANCIA, k=3, max_sobreposicao=1.0,
                               otimizar=otimizar)
    assert [r.rota.vertices for r in rs] == [["s", "d", "t"], ["s", "e", "t"], ["s", "f", "t"]]
    assert [r.distancia_km for r in rs] == pytest.approx([3.0, 4.0, 5.0])


def test_planejar_alternativas_otimizar_true_false_resumo_identico():
    G = _grafo_tres_vias()
    for criterio in Criterio:
        com = planejar_alternativas(G, "s", "t", criterio, k=3, max_sobreposicao=1.0, otimizar=True)
        sem = planejar_alternativas(G, "s", "t", criterio, k=3, max_sobreposicao=1.0, otimizar=False)
        assert [r.rota.vertices for r in com] == [r.rota.vertices for r in sem]
        assert [r.distancia_km for r in com] == pytest.approx([r.distancia_km for r in sem])
        assert [r.tempo_min for r in com] == pytest.approx([r.tempo_min for r in sem])
        assert [r.litros for r in com] == pytest.approx([r.litros for r in sem])
