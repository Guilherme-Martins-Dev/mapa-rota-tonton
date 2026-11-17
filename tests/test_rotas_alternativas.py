"""Rotas alternativas (Yen) e filtro de sobreposição. Só grafos sintéticos, sem rede."""
import copy
import itertools
import math
import random

import networkx as nx
import pytest

from tonton.rotas import (
    Rota,
    RotaInexistente,
    _sobreposicao,
    dijkstra,
    menor_peso_aresta,
    menor_rota,
    menores_rotas,
    rotas_alternativas,
)


def _foto(G):
    return (sorted(G.nodes(data=True), key=repr), sorted(G.edges(keys=True, data=True), key=repr))


def _grafo_aleatorio(seed, n=6, m=14):
    rng = random.Random(seed)
    G = nx.MultiDiGraph()
    G.add_nodes_from(range(n))
    for _ in range(m):
        u, v = rng.sample(range(n), 2)
        G.add_edge(u, v, t_atual=float(rng.randint(0, 3)), length=float(rng.randint(1, 4)))
    return G


def _forca_bruta(G, o, d, peso="t_atual"):
    """Custos (ordenados) de todos os caminhos sem laço; custo do trecho = menor paralela."""
    H = nx.DiGraph()
    H.add_nodes_from(G.nodes)
    for u, v in set((a, b) for a, b, _ in G.edges(keys=True)):
        H.add_edge(u, v, w=min(dd[peso] for dd in G[u][v].values()))
    caminhos = [[o]] if o == d else list(nx.all_simple_paths(H, o, d))
    return sorted(sum(H[a][b]["w"] for a, b in zip(c, c[1:])) for c in caminhos)


def _valida(G, rota, o, d, peso):
    assert rota.vertices[0] == o and rota.vertices[-1] == d
    assert len(set(rota.vertices)) == len(rota.vertices), "laço"
    assert len(rota.arestas) == len(rota.vertices) - 1
    for (u, v, k), a, b in zip(rota.arestas, rota.vertices, rota.vertices[1:]):
        assert (u, v) == (a, b) and k in G[u][v]
    assert rota.custo == pytest.approx(sum(G[u][v][k][peso] for u, v, k in rota.arestas))


# ---------- Yen contra força bruta ----------

@pytest.mark.parametrize("seed", range(30))
def test_yen_custos_coincidem_com_forca_bruta(seed):
    G = _grafo_aleatorio(seed)
    esperado = _forca_bruta(G, 0, 5)
    if not esperado:
        with pytest.raises(RotaInexistente):
            menores_rotas(G, 0, 5, k=5)
        return
    for k in (1, 3, len(esperado), len(esperado) + 4):
        rotas = menores_rotas(G, 0, 5, k=k)
        assert [r.custo for r in rotas] == pytest.approx(esperado[:k])
        assert len(rotas) == min(k, len(esperado))
        for r in rotas:
            _valida(G, r, 0, 5, "t_atual")
        sequencias = [tuple(r.vertices) for r in rotas]
        assert len(set(sequencias)) == len(sequencias)


@pytest.mark.parametrize("seed", range(30, 40))
def test_yen_denso_com_paralelas_e_empates(seed):
    G = _grafo_aleatorio(seed, n=5, m=22)  # muitas paralelas e pesos repetidos
    esperado = _forca_bruta(G, 0, 4)
    if not esperado:
        return
    rotas = menores_rotas(G, 0, 4, k=1000)
    assert [r.custo for r in rotas] == pytest.approx(esperado)
    for r in rotas:
        _valida(G, r, 0, 4, "t_atual")


def test_yen_usa_o_peso_pedido():
    testados = 0
    for seed in range(20):
        G = _grafo_aleatorio(seed)
        esperado = _forca_bruta(G, 0, 5, "length")
        if not esperado:
            continue
        rotas = menores_rotas(G, 0, 5, k=1000, peso="length")
        assert [r.custo for r in rotas] == pytest.approx(esperado)
        testados += 1
    assert testados >= 5


def test_primeira_e_menor_rota_e_custos_nao_decrescentes():
    for seed in range(15):
        G = _grafo_aleatorio(seed)
        try:
            melhor = menor_rota(G, 0, 5)
        except RotaInexistente:
            continue
        rotas = menores_rotas(G, 0, 5, k=6)
        assert rotas[0].custo == melhor.custo
        custos = [r.custo for r in rotas]
        assert custos == sorted(custos)


def test_k_maior_que_caminhos_existentes():
    G = nx.MultiDiGraph()
    G.add_edge("s", "a", t_atual=1.0)
    G.add_edge("a", "t", t_atual=1.0)
    G.add_edge("s", "t", t_atual=5.0)
    rotas = menores_rotas(G, "s", "t", k=10)
    assert [r.vertices for r in rotas] == [["s", "a", "t"], ["s", "t"]]


def test_k_um_devolve_so_a_melhor():
    G = _grafo_aleatorio(1)
    rotas = menores_rotas(G, 0, 5, k=1)
    assert len(rotas) == 1 and rotas[0].custo == menor_rota(G, 0, 5).custo


def test_origem_igual_destino():
    G = _grafo_aleatorio(2)
    rotas = menores_rotas(G, 0, 0, k=4)
    assert len(rotas) == 1 and rotas[0].vertices == [0] and rotas[0].arestas == [] and rotas[0].custo == 0.0


def test_destino_inalcancavel_levanta():
    G = nx.MultiDiGraph()
    G.add_edge("s", "a", t_atual=1.0)
    G.add_node("t")
    with pytest.raises(RotaInexistente):
        menores_rotas(G, "s", "t", k=3)
    with pytest.raises(RotaInexistente):
        rotas_alternativas(G, "s", "t", k=3)


def test_mao_unica_nao_volta():
    G = nx.MultiDiGraph()
    G.add_edge("a", "b", t_atual=1.0)
    G.add_edge("b", "c", t_atual=1.0)
    assert len(menores_rotas(G, "a", "c", k=5)) == 1
    with pytest.raises(RotaInexistente):
        menores_rotas(G, "c", "a", k=5)


def test_paralelas_contam_como_um_unico_caminho():
    """Identidade do caminho = sequência de vértices: paralelas não geram rotas repetidas."""
    G = nx.MultiDiGraph()
    G.add_edge("s", "a", t_atual=1.0)
    G.add_edge("s", "a", t_atual=3.0)
    G.add_edge("a", "t", t_atual=2.0)
    G.add_edge("a", "t", t_atual=2.5)
    rotas = menores_rotas(G, "s", "t", k=5)
    assert len(rotas) == 1
    assert rotas[0].custo == 3.0 and rotas[0].arestas == [("s", "a", 0), ("a", "t", 0)]


def test_quadro_segunda_melhor_e_39():
    G = nx.MultiDiGraph()
    G.add_edge("s", "b", t_atual=4.0)
    G.add_edge("b", "v", t_atual=35.0)
    G.add_edge("s", "a", t_atual=6.0)
    G.add_edge("a", "v", t_atual=32.0)
    rotas = menores_rotas(G, "s", "v", k=3)
    assert [(r.vertices, r.custo) for r in rotas] == [(["s", "a", "v"], 38.0), (["s", "b", "v"], 39.0)]


@pytest.mark.parametrize("k", [0, -1])
def test_k_invalido(k):
    G = _grafo_aleatorio(0)
    with pytest.raises(ValueError):
        menores_rotas(G, 0, 5, k=k)
    with pytest.raises(ValueError):
        rotas_alternativas(G, 0, 5, k=k)


@pytest.mark.parametrize("valor", [-0.01, 1.01, 2])
def test_max_sobreposicao_invalida(valor):
    with pytest.raises(ValueError):
        rotas_alternativas(_grafo_aleatorio(0), 0, 5, max_sobreposicao=valor)


def test_max_candidatos_invalido():
    with pytest.raises(ValueError):
        rotas_alternativas(_grafo_aleatorio(0), 0, 5, max_candidatos=0)


# ---------- ignorar_vertices / ignorar_arestas ----------

def _losango():
    G = nx.MultiDiGraph()
    G.add_edge("s", "a", t_atual=1.0)
    G.add_edge("a", "t", t_atual=1.0)
    G.add_edge("s", "b", t_atual=2.0)
    G.add_edge("b", "t", t_atual=2.0)
    return G


def test_ignorar_vertices_respeitado_e_sem_mutar():
    G = _losango()
    antes = _foto(G)
    r = menor_rota(G, "s", "t", ignorar_vertices={"a"})
    assert r.vertices == ["s", "b", "t"] and r.custo == 4.0
    dist, pred = dijkstra(G, "s", "t_atual", ignorar_vertices={"a"})
    assert "a" not in dist and "a" not in pred
    assert _foto(G) == antes


def test_ignorar_arestas_respeitado_e_sem_mutar():
    G = _losango()
    antes = _foto(G)
    r = menor_rota(G, "s", "t", ignorar_arestas={("a", "t", 0)})
    assert r.vertices == ["s", "b", "t"]
    assert _foto(G) == antes
    assert menor_rota(G, "s", "t").vertices == ["s", "a", "t"]


def test_ignorar_todas_as_saidas_torna_inalcancavel():
    G = _losango()
    with pytest.raises(RotaInexistente):
        menor_rota(G, "s", "t", ignorar_arestas={("a", "t", 0), ("b", "t", 0)})


def test_ignorar_destino_levanta():
    with pytest.raises(RotaInexistente):
        menor_rota(_losango(), "s", "t", ignorar_vertices={"t"})


def test_ignorar_paralela_usa_a_outra():
    G = nx.MultiDiGraph()
    G.add_edge("s", "t", t_atual=1.0)  # chave 0
    G.add_edge("s", "t", t_atual=2.0)  # chave 1
    assert menor_peso_aresta(G, "s", "t", "t_atual") == (0, 1.0)
    assert menor_peso_aresta(G, "s", "t", "t_atual", ignorar_arestas={("s", "t", 0)}) == (1, 2.0)
    r = menor_rota(G, "s", "t", ignorar_arestas={("s", "t", 0)})
    assert r.arestas == [("s", "t", 1)] and r.custo == 2.0
    chave, w = menor_peso_aresta(G, "s", "t", "t_atual", ignorar_arestas={("s", "t", 0), ("s", "t", 1)})
    assert chave is None and math.isinf(w)


def test_yen_proibir_trecho_proibe_todas_as_paralelas():
    """Se a 2ª rota pudesse reusar o trecho s->a por outra paralela, haveria duplicata s,a,t."""
    G = nx.MultiDiGraph()
    for w in (1.0, 2.0, 3.0):
        G.add_edge("s", "a", t_atual=w)
    G.add_edge("a", "t", t_atual=1.0)
    G.add_edge("s", "t", t_atual=10.0)
    rotas = menores_rotas(G, "s", "t", k=5)
    assert [r.vertices for r in rotas] == [["s", "a", "t"], ["s", "t"]]


def test_menores_rotas_nao_muta_o_grafo():
    G = _grafo_aleatorio(4)
    antes = _foto(G)
    menores_rotas(G, 0, 5, k=20)
    rotas_alternativas(G, 0, 5, k=5)
    assert _foto(G) == antes


# ---------- rotas_alternativas e _sobreposicao ----------

def _grafo_quase_duplicata():
    """Melhor s,a,b,t (3000 m). s,a,x,b,t (4000 m) repete 2000 m dela (0,5); s,y,t (5000 m) é disjunta."""
    G = nx.MultiDiGraph()
    for u, v, c in [("s", "a", 1000), ("a", "b", 1000), ("b", "t", 1000),
                    ("a", "x", 1000), ("x", "b", 1000),
                    ("s", "y", 2500), ("y", "t", 2500)]:
        G.add_edge(u, v, length=float(c))
    return G


def test_yen_puro_da_quase_duplicata_e_filtro_escolhe_outra_via():
    G = _grafo_quase_duplicata()
    puro = menores_rotas(G, "s", "t", k=3, peso="length")
    assert [r.vertices for r in puro] == [["s", "a", "b", "t"], ["s", "a", "x", "b", "t"], ["s", "y", "t"]]
    filtrado = rotas_alternativas(G, "s", "t", k=2, peso="length", max_sobreposicao=0.4)
    assert [r.vertices for r in filtrado] == [["s", "a", "b", "t"], ["s", "y", "t"]]


def test_limite_de_sobreposicao_e_inclusivo():
    G = _grafo_quase_duplicata()
    r = rotas_alternativas(G, "s", "t", k=2, peso="length", max_sobreposicao=0.5)
    assert r[1].vertices == ["s", "a", "x", "b", "t"]


def test_max_sobreposicao_um_nao_filtra():
    G = _grafo_quase_duplicata()
    com = rotas_alternativas(G, "s", "t", k=3, peso="length", max_sobreposicao=1.0)
    puro = menores_rotas(G, "s", "t", k=3, peso="length")
    assert [r.vertices for r in com] == [r.vertices for r in puro]


def test_max_sobreposicao_zero_so_aceita_sem_arestas_em_comum():
    G = _grafo_quase_duplicata()
    rotas = rotas_alternativas(G, "s", "t", k=5, peso="length", max_sobreposicao=0.0)
    assert [r.vertices for r in rotas] == [["s", "a", "b", "t"], ["s", "y", "t"]]
    for a, b in itertools.combinations(rotas, 2):
        assert not set(a.arestas) & set(b.arestas)


def test_alternativas_primeira_e_a_melhor_e_k_um():
    G = _grafo_quase_duplicata()
    r = rotas_alternativas(G, "s", "t", k=1, peso="length")
    assert len(r) == 1 and r[0].custo == menor_rota(G, "s", "t", "length").custo


def test_max_candidatos_limita_a_busca():
    G = _grafo_quase_duplicata()
    # só a melhor e a quase-duplicata são examinadas: a disjunta nem entra
    r = rotas_alternativas(G, "s", "t", k=3, peso="length", max_sobreposicao=0.4, max_candidatos=2)
    assert [x.vertices for x in r] == [["s", "a", "b", "t"]]


def test_alternativas_origem_igual_destino():
    G = _grafo_quase_duplicata()
    r = rotas_alternativas(G, "s", "s", k=3)
    assert len(r) == 1 and r[0].vertices == ["s"]


def _rota(arestas):
    return Rota([a[0] for a in arestas] + [arestas[-1][1]], arestas, 0.0, "length")


def test_sobreposicao_identicas_e_disjuntas():
    G = nx.MultiDiGraph()
    G.add_edge("a", "b", length=100.0)
    G.add_edge("b", "c", length=300.0)
    G.add_edge("a", "x", length=50.0)
    r = _rota([("a", "b", 0), ("b", "c", 0)])
    assert _sobreposicao(G, r, [set(r.arestas)]) == 1.0
    assert _sobreposicao(G, r, [{("a", "x", 0)}]) == 0.0
    assert _sobreposicao(G, r, [{("b", "c", 0)}]) == pytest.approx(0.75)  # ponderado por metros


def test_sobreposicao_usa_o_maximo_de_uma_so_rota_aceita():
    G = nx.MultiDiGraph()
    G.add_edge("a", "b", length=100.0)
    G.add_edge("b", "c", length=100.0)
    r = _rota([("a", "b", 0), ("b", "c", 0)])
    assert _sobreposicao(G, r, [{("a", "b", 0)}, {("b", "c", 0)}]) == pytest.approx(0.5)


def test_sobreposicao_sem_length_conta_zero():
    G = nx.MultiDiGraph()
    G.add_edge("a", "b")  # sem length
    G.add_edge("b", "c", length=100.0)
    G.add_edge("c", "d", length=float("nan"))
    r1 = _rota([("a", "b", 0), ("b", "c", 0)])
    assert _sobreposicao(G, r1, [{("a", "b", 0)}]) == 0.0
    assert _sobreposicao(G, r1, [{("b", "c", 0)}]) == 1.0  # aresta sem length some do total
    r2 = _rota([("a", "b", 0), ("c", "d", 0)])  # total 0: sem divisão por zero
    assert _sobreposicao(G, r2, [set(r2.arestas)]) == 0.0


def test_alternativas_em_grafo_aleatorio_sao_validas_e_ordenadas():
    for seed in range(20):
        G = _grafo_aleatorio(seed)
        try:
            rotas = rotas_alternativas(G, 0, 5, k=4, peso="length", max_sobreposicao=0.6)
        except RotaInexistente:
            continue
        assert rotas[0].custo == menor_rota(G, 0, 5, "length").custo
        custos = [r.custo for r in rotas]
        assert custos == sorted(custos) and len(rotas) <= 4
        for r in rotas:
            _valida(G, r, 0, 5, "length")
        for i, c in enumerate(rotas[1:], 1):
            for anterior in rotas[:i]:
                assert tuple(c.vertices) != tuple(anterior.vertices)
