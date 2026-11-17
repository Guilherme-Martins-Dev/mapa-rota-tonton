import math
import random
import time

import networkx as nx
import pytest

from tonton import pesos
from tonton.rotas import Rota, RotaInexistente, dijkstra, menor_peso_aresta, menor_rota


def soma(G, rota, peso):
    return sum(G[u][v][k][peso] for u, v, k in rota.arestas)


def test_quadro_relaxamento_38_vence_39():
    # dois caminhos s->v: via b (4+35=39, visitado primeiro) e via a (6+32=38)
    G = nx.MultiDiGraph()
    G.add_edge("s", "b", t_atual=4.0)
    G.add_edge("b", "v", t_atual=35.0)
    G.add_edge("s", "a", t_atual=6.0)
    G.add_edge("a", "v", t_atual=32.0)
    dist, pred = dijkstra(G, "s")
    assert dist["v"] == 38.0 and dist["v"] != 39.0
    r = menor_rota(G, "s", "v")
    assert r.custo == 38.0
    assert r.vertices == ["s", "a", "v"]


def test_relaxamento_tardio():
    G = nx.MultiDiGraph()
    G.add_edge(1, 4, t_atual=100.0)  # alcança 4 caro primeiro
    G.add_edge(1, 2, t_atual=1.0)
    G.add_edge(2, 3, t_atual=1.0)
    G.add_edge(3, 4, t_atual=1.0)
    r = menor_rota(G, 1, 4)
    assert r.custo == 3.0 and r.vertices == [1, 2, 3, 4]


def test_arestas_paralelas_menor_peso_e_chave():
    G = nx.MultiDiGraph()
    k700 = G.add_edge("u", "v", t_atual=700.0)
    k500 = G.add_edge("u", "v", t_atual=500.0)
    r = menor_rota(G, "u", "v")
    assert r.custo == 500.0 and r.arestas == [("u", "v", k500)] and k500 != k700
    # empate: menor chave
    H = nx.MultiDiGraph()
    H.add_edge("u", "v", t_atual=5.0)
    H.add_edge("u", "v", t_atual=5.0)
    assert menor_rota(H, "u", "v").arestas == [("u", "v", 0)]
    # inf numa delas é ignorado
    I = nx.MultiDiGraph()
    I.add_edge("u", "v", t_atual=math.inf)
    k = I.add_edge("u", "v", t_atual=9.0)
    assert menor_peso_aresta(I, "u", "v", "t_atual") == (k, 9.0)
    assert menor_rota(I, "u", "v").custo == 9.0


def test_mao_unica():
    G = nx.MultiDiGraph()
    G.add_edge("v", "u", t_atual=3.0)
    with pytest.raises(RotaInexistente):
        menor_rota(G, "u", "v")
    assert menor_rota(G, "v", "u").custo == 3.0


def test_inalcancavel_componentes_desconexos():
    G = nx.MultiDiGraph()
    G.add_edge(1, 2, t_atual=1.0)
    G.add_edge(3, 4, t_atual=1.0)
    with pytest.raises(RotaInexistente, match="1.*4"):
        menor_rota(G, 1, 4)


def test_vertice_inexistente():
    G = nx.MultiDiGraph()
    G.add_edge(1, 2, t_atual=1.0)
    with pytest.raises(RotaInexistente, match="99"):
        menor_rota(G, 99, 2)
    with pytest.raises(RotaInexistente, match="77"):
        menor_rota(G, 1, 77)


def test_origem_igual_destino():
    G = nx.MultiDiGraph()
    G.add_edge(1, 2, t_atual=1.0)
    assert menor_rota(G, 1, 1) == Rota([1], [], 0.0, "t_atual")


def test_pesos_diferentes_rotas_diferentes():
    G = nx.MultiDiGraph()
    # curta (length) mas lenta; longa mas rápida; com trânsito a rápida piora
    G.add_edge("a", "b", length=1000.0, t_livre=250.0, t_atual=900.0)
    G.add_edge("a", "c", length=3000.0, t_livre=100.0, t_atual=150.0)
    G.add_edge("c", "b", length=3000.0, t_livre=100.0, t_atual=150.0)
    G.add_edge("c", "d", length=1.0, t_livre=1.0, t_atual=1.0)
    rl = menor_rota(G, "a", "b", "length")
    rv = menor_rota(G, "a", "b", "t_livre")
    ra = menor_rota(G, "a", "b", "t_atual")
    assert rl.vertices == ["a", "b"] and rl.peso == "length" and rl.custo == 1000.0
    assert rv.vertices == ["a", "c", "b"] and rv.custo == 200.0 and rv.peso == "t_livre"
    assert ra.vertices == ["a", "c", "b"] and ra.custo == 300.0
    G["a"]["b"][0]["t_livre"] = 150.0
    assert menor_rota(G, "a", "b", "t_livre").vertices == ["a", "b"]


def test_peso_ausente_e_negativo():
    G = nx.MultiDiGraph()
    G.add_edge(1, 2, length=5.0)
    with pytest.raises(KeyError):
        menor_rota(G, 1, 2, "t_atual")
    N = nx.MultiDiGraph()
    N.add_edge(1, 2, t_atual=-1.0)
    with pytest.raises(ValueError):
        menor_rota(N, 1, 2)


def test_t_atual_inf():
    G = nx.MultiDiGraph()
    G.add_edge(1, 2, t_atual=math.inf)
    G.add_edge(1, 3, t_atual=10.0)
    G.add_edge(3, 2, t_atual=10.0)
    assert menor_rota(G, 1, 2).vertices == [1, 3, 2]
    U = nx.MultiDiGraph()
    U.add_edge(1, 2, t_atual=math.inf)
    with pytest.raises(RotaInexistente):
        menor_rota(U, 1, 2)


def grafo_aleatorio(semente, n=200, m=800):
    rnd = random.Random(semente)
    G = nx.MultiDiGraph()
    G.add_nodes_from(range(n))
    for _ in range(m):
        u, v = rnd.randrange(n), rnd.randrange(n)
        if u == v:
            continue
        for _ in range(rnd.choice([1, 1, 2])):  # paralelas
            G.add_edge(u, v, t_atual=rnd.uniform(1, 100), t_livre=rnd.uniform(1, 100),
                       length=rnd.uniform(10, 1000))
    return G


@pytest.mark.parametrize("peso", ["t_atual", "t_livre", "length"])
def test_comparacao_com_networkx(peso):
    G = grafo_aleatorio(42, n=200, m=450)  # esparso: alguns pares sem caminho
    rnd = random.Random(7)
    achou = sem = 0
    for _ in range(50):
        s, t = rnd.randrange(200), rnd.randrange(200)
        try:
            esperado = nx.shortest_path_length(G, s, t, weight=peso)
        except nx.NetworkXNoPath:
            with pytest.raises(RotaInexistente):
                menor_rota(G, s, t, peso)
            sem += 1
            continue
        r = menor_rota(G, s, t, peso)
        assert r.custo == pytest.approx(esperado)
        assert soma(G, r, peso) == pytest.approx(r.custo)
        achou += 1
    assert achou > 0


def test_desempenho_5k_vertices():
    G = grafo_aleatorio(1, n=5000, m=15000)
    t0 = time.perf_counter()
    try:
        menor_rota(G, 0, 4999)
    except RotaInexistente:
        pass
    assert time.perf_counter() - t0 < 1.0


def test_integracao_atribuir_pesos_sem_rede():
    G = nx.MultiDiGraph()
    G.add_node(1, x=-38.50, y=-3.80)
    G.add_node(2, x=-38.49, y=-3.80)
    G.add_node(3, x=-38.48, y=-3.80)
    G.add_edge(1, 2, length=1000.0, highway="primary", maxspeed="50")
    G.add_edge(2, 3, length=500.0, highway="residential")
    G.add_edge(2, 3, length=700.0, highway="residential")
    pesos.atribuir_pesos(G, consultar=None)
    r = menor_rota(G, 1, 3, "t_atual")
    assert r.vertices == [1, 2, 3]
    assert r.custo == pytest.approx(1000 / (50 / 3.6) + 500 / (30 / 3.6))
    assert soma(G, r, "t_atual") == pytest.approx(r.custo)
