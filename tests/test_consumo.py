import dataclasses
import math

import networkx as nx
import pytest

from tonton import consumo, pesos
from tonton.consumo import (
    PADRAO,
    Veiculo,
    atribuir_consumo,
    consumo_l_por_100km,
    litros,
    rota_menor_consumo,
    velocidade_otima_kmh,
)
from tonton.rotas import RotaInexistente, menor_rota


def test_formato_de_u():
    assert consumo_l_por_100km(20) > consumo_l_por_100km(65) < consumo_l_por_100km(120)


def test_minimo_perto_de_65():
    v_star = velocidade_otima_kmh(PADRAO)
    assert v_star == pytest.approx(65, abs=1.5)
    minimo = consumo_l_por_100km(v_star)
    for v in range(10, 151, 5):
        assert consumo_l_por_100km(v) >= minimo - 1e-9


def test_valores_conhecidos():
    assert consumo_l_por_100km(65) == pytest.approx(6.50, abs=0.05)
    assert consumo_l_por_100km(velocidade_otima_kmh(PADRAO)) == pytest.approx(6.50, abs=0.05)
    assert litros(1000, 65) == pytest.approx(0.065, abs=0.001)
    assert litros(0, 65) == 0.0


def test_piso_para_velocidade_invalida():
    esperado = consumo_l_por_100km(5.0)
    assert esperado == pytest.approx(33.05, abs=0.05)
    for v in (None, math.nan, 0, 0.0, -10, 3):
        assert consumo_l_por_100km(v) == pytest.approx(esperado)
    assert litros(1000, 0) == pytest.approx(esperado / 100)
    assert litros(1000, None) == pytest.approx(esperado / 100)


def test_piso_do_veiculo_customizado():
    v = Veiculo("x", a=1.0, b=100.0, c=0.001, v_piso_kmh=10.0)
    assert consumo_l_por_100km(0, v) == pytest.approx(consumo_l_por_100km(10, v))
    assert consumo_l_por_100km(10, v) == pytest.approx(1.0 + 10.0 + 0.1)


def test_comprimento_none_vira_inf():
    assert litros(None, 60) == math.inf


def test_veiculo_frozen_e_outro_veiculo_muda_resultado():
    with pytest.raises(dataclasses.FrozenInstanceError):
        PADRAO.a = 1.0
    beberrao = Veiculo("suv", a=5.0, b=200.0, c=4e-4)
    assert consumo_l_por_100km(65, beberrao) > consumo_l_por_100km(65, PADRAO)
    assert litros(1000, 65, beberrao) > litros(1000, 65, PADRAO)
    assert velocidade_otima_kmh(beberrao) != pytest.approx(velocidade_otima_kmh(PADRAO))


def test_atribuir_consumo_todas_arestas_inclusive_paralelas():
    G = nx.MultiDiGraph()
    G.add_edge("a", "b", length=1000.0, v_atual=65.0, name=["Rua X", "Rua Y"])
    G.add_edge("a", "b", length=2000.0, v_atual=30.0)  # paralela, sem name
    G.add_edge("b", "c", length=500.0, v_atual=100.0)  # mão única
    antes = {(u, v, k): dict(d) for u, v, k, d in G.edges(keys=True, data=True)}
    nos_antes = {n: dict(d) for n, d in G.nodes(data=True)}
    r = atribuir_consumo(G)
    assert r is G
    for u, v, k, d in G.edges(keys=True, data=True):
        assert d["litros"] == pytest.approx(litros(d["length"], d["v_atual"]))
        sem = {kk: vv for kk, vv in d.items() if kk != "litros"}
        assert sem == antes[(u, v, k)]
    assert {n: dict(d) for n, d in G.nodes(data=True)} == nos_antes
    assert G.number_of_edges() == 3
    assert G["a"]["b"][0]["litros"] != G["a"]["b"][1]["litros"]


def test_atribuir_consumo_fallback_sem_v_atual():
    G = nx.MultiDiGraph()
    G.add_edge("a", "b", length=1000.0, highway="residential")
    G.add_edge("b", "c", length=1000.0, maxspeed="80")
    atribuir_consumo(G)
    v1 = pesos.velocidade_livre_osm(G["a"]["b"][0])
    assert G["a"]["b"][0]["litros"] == pytest.approx(litros(1000, v1))
    assert G["b"]["c"][0]["litros"] == pytest.approx(litros(1000, 80.0))


def test_atribuir_consumo_sem_length_e_inf():
    G = nx.MultiDiGraph()
    G.add_edge("a", "b", v_atual=50.0)
    atribuir_consumo(G)
    assert G["a"]["b"][0]["litros"] == math.inf


def test_atribuir_consumo_velocidade_zero_nao_quebra():
    G = nx.MultiDiGraph()
    G.add_edge("a", "b", length=1000.0, v_atual=0.0)
    atribuir_consumo(G)
    assert math.isfinite(G["a"]["b"][0]["litros"])


def _grafo_tres_rotas():
    """s->t por tres vias: direta curta e congestionada, rodovia rapida, e via economica a 65."""
    G = nx.MultiDiGraph()
    # (comprimento m, v_atual km/h)
    vias = {"d": (3000.0, 20.0), "f": (5000.0, 120.0), "e": (4000.0, 65.0)}
    for meio, (comp, v) in vias.items():
        G.add_edge("s", meio, length=comp / 2, v_atual=v)
        G.add_edge(meio, "t", length=comp / 2, v_atual=v)
    for _, _, d in G.edges(data=True):
        d["t_atual"] = pesos.tempo(d["length"], d["v_atual"])
    atribuir_consumo(G)
    return G


def test_menor_tempo_menor_consumo_e_menor_distancia_divergem():
    G = _grafo_tres_rotas()
    por_tempo = menor_rota(G, "s", "t", peso="t_atual")
    por_dist = menor_rota(G, "s", "t", peso="length")
    por_litros = rota_menor_consumo(G, "s", "t")
    assert por_tempo.vertices == ["s", "f", "t"]   # 120 km/h
    assert por_dist.vertices == ["s", "d", "t"]    # 3 km
    assert por_litros.vertices == ["s", "e", "t"]  # ~65 km/h
    assert por_litros.custo == pytest.approx(litros(4000, 65))
    # a rapida gasta mais que a economica
    assert litros(5000, 120) > litros(4000, 65)
    assert litros(3000, 20) > litros(4000, 65)


def test_rota_menor_consumo_com_paralela_escolhe_a_economica():
    G = nx.MultiDiGraph()
    G.add_edge("s", "t", length=1000.0, v_atual=130.0)
    k = G.add_edge("s", "t", length=1000.0, v_atual=65.0)
    atribuir_consumo(G)
    r = rota_menor_consumo(G, "s", "t")
    assert r.arestas == [("s", "t", k)]


def test_rota_menor_consumo_respeita_mao_unica_e_inalcancavel():
    G = nx.MultiDiGraph()
    G.add_edge("s", "t", length=1000.0, v_atual=65.0)
    atribuir_consumo(G)
    assert rota_menor_consumo(G, "s", "t").vertices == ["s", "t"]
    with pytest.raises(RotaInexistente):
        rota_menor_consumo(G, "t", "s")


def test_gravar_litros_igual_a_formula_e_a_atribuir_consumo():
    from tonton.consumo import gravar_litros

    G = nx.MultiDiGraph()
    G.add_edge(1, 2, length=3000.0, v_atual=40.0, highway="primary")
    G.add_edge(2, 3, length=1000.0, highway="primary")  # sem v_atual: velocidade livre do OSM (50)
    G.add_edge(3, 4, highway="primary", v_atual=40.0)    # sem length: inf
    isolada = {k: dict(G.edges[k]) for k in G.edges}
    for d in isolada.values():
        gravar_litros(d)
    atribuir_consumo(G)
    for k, d in isolada.items():
        assert d["litros"] == G.edges[k]["litros"]
    assert isolada[(1, 2, 0)]["litros"] == pytest.approx(3 * consumo_l_por_100km(40.0) / 100)
    assert isolada[(2, 3, 0)]["litros"] == pytest.approx(consumo_l_por_100km(50.0) / 100)
    assert isolada[(3, 4, 0)]["litros"] == math.inf
