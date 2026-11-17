import math

import networkx as nx
import pytest

from tonton import pesos


def grafo():
    G = nx.MultiDiGraph()
    G.add_node(1, x=-38.50, y=-3.80)
    G.add_node(2, x=-38.49, y=-3.80)
    G.add_node(3, x=-38.48, y=-3.80)
    G.add_edge(1, 2, length=1000.0, highway="primary", maxspeed="50")
    G.add_edge(2, 3, length=500.0, highway="residential")
    G.add_edge(2, 3, length=700.0, highway="residential")  # rua paralela
    return G


@pytest.mark.parametrize("valor,esperado", [
    ("40", 40.0), ("40 km/h", 40.0), (["30", "50"], 30.0), ("30 mph", 30 * 1.609344),
    (None, None), ("walk", None), ("0", None), ("", None),
])
def test_ler_maxspeed(valor, esperado):
    r = pesos.ler_maxspeed(valor)
    assert r == pytest.approx(esperado) if esperado is not None else r is None


def test_tempo_e_comprimento_sobre_velocidade():
    assert pesos.tempo(1000, 36) == pytest.approx(100.0)  # 36 km/h = 10 m/s
    assert pesos.tempo(None, 36) == math.inf
    assert pesos.tempo(1000, 0) == math.inf
    assert pesos.tempo(1000, None) == math.inf


def test_fallback_por_tipo_de_via():
    assert pesos.velocidade_livre_osm({"highway": "residential"}) == 30
    assert pesos.velocidade_livre_osm({"highway": ["service", "primary"]}) == 20
    assert pesos.velocidade_livre_osm({"highway": "xyz"}) == pesos.VELOCIDADE_GERAL
    assert pesos.velocidade_livre_osm({"highway": "primary", "maxspeed": "70"}) == 70


def test_sem_consulta_atual_igual_livre():
    G = pesos.atribuir_pesos(grafo())
    d = G.edges[1, 2, 0]
    assert d["v_livre"] == d["v_atual"] == 50
    assert d["t_livre"] == d["t_atual"] == pytest.approx(72.0)


def test_tomtom_so_nas_vias_principais_e_com_cache():
    chamadas = []

    def consultar(lat, lon):
        chamadas.append((lat, lon))
        return {"freeFlowSpeed": 50, "currentSpeed": 25}

    G = pesos.atribuir_pesos(grafo(), consultar)
    assert len(chamadas) == 1  # residential não consulta
    d = G.edges[1, 2, 0]
    assert d["t_atual"] == pytest.approx(2 * d["t_livre"])
    assert G.edges[2, 3, 0]["t_atual"] == G.edges[2, 3, 0]["t_livre"]


def test_falha_da_tomtom_cai_no_fallback():
    def consultar(lat, lon):
        raise RuntimeError("cota estourada")

    G = pesos.atribuir_pesos(grafo(), consultar)
    d = G.edges[1, 2, 0]
    assert d["v_atual"] == d["v_livre"] == 50


@pytest.mark.parametrize("fluxo", [{}, {"currentSpeed": 0, "freeFlowSpeed": 40}, {"currentSpeed": "x", "freeFlowSpeed": 40}])
def test_fluxo_invalido_cai_no_fallback(fluxo):
    G = pesos.atribuir_pesos(grafo(), lambda lat, lon: fluxo)
    assert G.edges[1, 2, 0]["v_atual"] == 50


def test_aresta_sem_comprimento_vira_infinito():
    G = grafo()
    G.add_edge(3, 1, highway="residential")
    pesos.atribuir_pesos(G)
    assert G.edges[3, 1, 0]["t_livre"] == math.inf


def test_gravar_velocidades_grava_os_mesmos_atributos_de_atribuir_pesos():
    from tonton.pesos import gravar_velocidades, tempo

    dados = {"length": 500.0}
    gravar_velocidades(dados, 50.0, 25.0)
    assert dados["v_livre"] == 50.0 and dados["v_atual"] == 25.0
    assert dados["t_livre"] == tempo(500.0, 50.0) == pytest.approx(500.0 / (50.0 / 3.6))
    assert dados["t_atual"] == tempo(500.0, 25.0)
    sem = {}
    gravar_velocidades(sem, 50.0, 25.0)
    assert sem["t_livre"] == math.inf and sem["t_atual"] == math.inf
