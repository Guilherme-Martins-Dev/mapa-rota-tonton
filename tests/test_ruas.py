import math

import networkx as nx
import pytest
from shapely.geometry import LineString

from tonton import ruas
from tonton.ruas import (
    Trecho, agrupar_por_rua, buscar_rua, como_lista, eh_tomtom,
    normalizar, ponto_medio, tem_nome, trechos,
)

TOMTOM = {"trunk", "primary", "secondary", "tertiary"}


def novo_grafo():
    G = nx.MultiDiGraph()
    G.add_node(1, y=-3.80, x=-38.50)
    G.add_node(2, y=-3.82, x=-38.54)
    G.add_node(3, y=-3.90, x=-38.60)
    G.add_node(4, y=-3.80, x=-38.50)  # coincide com o 1
    return G


def grafo_misto():
    G = novo_grafo()
    G.add_edge(1, 2, 0, name="Rua Jose", highway="residential", length=100.0)
    G.add_edge(2, 3, 0, name=["Avenida Padre José Nilson", "CE-010"], highway=["tertiary", "residential"], length=200.0)
    G.add_edge(2, 3, 1, highway="primary", length=210.0)
    G.add_edge(3, 1, 0, name="Avenida Dedé", highway="primary_link", length=50.0)
    return G


# --- normalização e nome ---

def test_normalizar_colapsa_espacos():
    assert normalizar("  Avenida  Washington Soares ") == "avenida washington soares"


def test_normalizar_acentos_e_caixa():
    assert normalizar("Açaí") == normalizar("ACAI") == "acai"


def test_como_lista():
    assert como_lista(None) == []
    assert como_lista("a") == ["a"]
    assert como_lista(["a", "b"]) == ["a", "b"]
    assert como_lista(("a", "b")) == ["a", "b"]
    assert sorted(como_lista({"a", "b"})) == ["a", "b"]


def test_tem_nome_vazio():
    assert tem_nome({}) is False
    assert tem_nome({"name": ""}) is False
    assert tem_nome({"name": ["", "  "]}) is False


def test_tem_nome_com_nome():
    assert tem_nome({"name": "Rua A"}) is True


def test_tem_nome_busca_em_lista():
    assert tem_nome({"name": ["Rua A", "Rua B"]}, "rua b") is True
    assert tem_nome({"name": ["Rua A", "Rua B"]}, "rua c") is False


def test_tem_nome_busca_sem_acento():
    assert tem_nome({"name": "Avenida Padre José Nilson"}, "jose") is True


@pytest.mark.parametrize("busca", ["", "   "])
def test_busca_vazia_levanta_valueerror(busca):
    with pytest.raises(ValueError):
        tem_nome({"name": "Rua A"}, busca)
    with pytest.raises(ValueError):
        buscar_rua(grafo_misto(), busca)


# --- trecho ---

def test_nomes_em_lista():
    ts = {(t.u, t.v, t.chave): t for t in trechos(grafo_misto())}
    assert ts[(2, 3, 0)].nomes == ("Avenida Padre José Nilson", "CE-010")


def test_nomes_sem_vazios_nem_duplicados():
    G = novo_grafo()
    G.add_edge(1, 2, name=["A", "", "A", "B"], highway="primary", length=1.0)
    assert next(trechos(G)).nomes == ("A", "B")


def test_sem_nome_aparece_em_trechos():
    ts = {(t.u, t.v, t.chave): t for t in trechos(grafo_misto())}
    assert ts[(2, 3, 1)].nomes == ()


def test_eh_tomtom():
    assert eh_tomtom({"highway": ["tertiary", "residential"]}) is True
    assert eh_tomtom({"highway": "primary_link"}) is False
    assert eh_tomtom({"highway": "residential"}) is False
    assert eh_tomtom({}) is False


# --- geometria ---

def test_ponto_medio_reto_sem_geometry():
    G = novo_grafo()
    G.add_edge(1, 2, 0, length=1.0)
    lat, lon = ponto_medio(G, 1, 2, 0)
    assert lat == pytest.approx((-3.80 + -3.82) / 2)
    assert lon == pytest.approx((-38.50 + -38.54) / 2)


def test_ponto_medio_em_L_nao_e_media_dos_vertices():
    G = nx.MultiDiGraph()
    G.add_node(1, y=0.0, x=0.0)
    G.add_node(2, y=1.0, x=3.0)
    # (lon, lat): 3 de comprimento na horizontal, depois 1 na vertical; metade = 2.0 -> (x=2, y=0)
    G.add_edge(1, 2, 0, geometry=LineString([(0, 0), (3, 0), (3, 1)]), length=4.0)
    lat, lon = ponto_medio(G, 1, 2, 0)
    assert (lat, lon) == pytest.approx((0.0, 2.0))
    media = (1 / 3, 2.0)  # média dos vértices: lat 1/3, lon 2.0
    assert lat != pytest.approx(media[0])


def test_ordem_lat_lon_assimetrica():
    G = nx.MultiDiGraph()
    G.add_node(1, y=10.0, x=50.0)
    G.add_node(2, y=20.0, x=70.0)
    G.add_edge(1, 2, 0, length=1.0)
    assert ponto_medio(G, 1, 2, 0) == pytest.approx((15.0, 60.0))


def test_comprimento_zero():
    G = novo_grafo()
    G.add_edge(1, 4, 0, length=0.0)
    assert ponto_medio(G, 1, 4, 0) == pytest.approx((-3.80, -38.50))
    G.add_edge(1, 4, 1, geometry=LineString([(-38.5, -3.8), (-38.5, -3.8)]), length=0.0)
    assert ponto_medio(G, 1, 4, 1) == pytest.approx((-3.80, -38.50))


def test_meio_dentro_da_bbox_e_coordenadas_da_messejana():
    G = grafo_misto()
    for t in trechos(G):
        lat, lon = t.meio
        assert -90 <= lat <= 90
        ys = [G.nodes[t.u]["y"], G.nodes[t.v]["y"]]
        xs = [G.nodes[t.u]["x"], G.nodes[t.v]["x"]]
        assert min(ys) - 1e-9 <= lat <= max(ys) + 1e-9
        assert min(xs) - 1e-9 <= lon <= max(xs) + 1e-9
        assert -4.0 < lat < -3.7 and -38.7 < lon < -38.4


def test_meio_equidistante_em_trecho_reto():
    G = novo_grafo()
    G.add_edge(1, 2, 0, length=1.0)
    lat, lon = ponto_medio(G, 1, 2, 0)

    def metros(a, b):
        dy = (a[0] - b[0]) * 111_320
        dx = (a[1] - b[1]) * 111_320 * math.cos(math.radians(a[0]))
        return math.hypot(dx, dy)

    ini = (G.nodes[1]["y"], G.nodes[1]["x"])
    fim = (G.nodes[2]["y"], G.nodes[2]["x"])
    assert abs(metros((lat, lon), ini) - metros((lat, lon), fim)) < 1.0


# --- estrutura ---

def test_arestas_paralelas():
    G = novo_grafo()
    G.add_edge(1, 2, 0, name="A", highway="primary", length=1.0)
    G.add_edge(1, 2, 1, name="B", highway="primary", length=2.0)
    ts = list(trechos(G))
    assert len(ts) == 2
    assert {t.chave for t in ts} == {0, 1}


def test_mao_unica_sem_reverso():
    G = novo_grafo()
    G.add_edge(1, 2, 0, length=1.0)
    ts = list(trechos(G))
    assert len(ts) == 1 and (ts[0].u, ts[0].v) == (1, 2)
    assert not G.has_edge(2, 1)


def test_proximo_igual_v_e_contagem():
    G = grafo_misto()
    ts = list(trechos(G))
    assert len(ts) == G.number_of_edges()
    assert all(t.proximo == t.v for t in ts)
    assert all(isinstance(t, Trecho) for t in ts)


def test_tipos_tupla_para_str_lista_ou_ausente():
    G = novo_grafo()
    G.add_edge(1, 2, 0, name="A", highway="primary", length=1.0)
    G.add_edge(1, 2, 1, name=["A", "B"], highway=["primary", "tertiary"], length=1.0)
    G.add_edge(2, 3, 0, length=1.0)
    for t in trechos(G):
        assert isinstance(t.nomes, tuple) and isinstance(t.highway, tuple)


def test_comprimento_ausente_e_none():
    G = novo_grafo()
    G.add_edge(1, 2, 0, name="A")
    assert next(trechos(G)).comprimento is None


def test_so_tomtom():
    ts = list(trechos(grafo_misto(), so_tomtom=True))
    assert len(ts) == 2
    for t in ts:
        assert set(t.highway) & TOMTOM
    assert {(t.u, t.v, t.chave) for t in ts} == {(2, 3, 0), (2, 3, 1)}


def test_buscar_rua():
    G = grafo_misto()
    achados = buscar_rua(G, "RUA JOSÉ")
    assert [(t.u, t.v) for t in achados] == [(1, 2)]
    assert buscar_rua(G, "inexistente") == []


def test_buscar_rua_insensivel_a_caixa_e_acento():
    G = grafo_misto()
    a = buscar_rua(G, "avenida")
    assert len(a) == 2
    assert a == buscar_rua(G, "AVENIDA") == buscar_rua(G, "Avénida")


def test_buscar_rua_so_tomtom():
    G = grafo_misto()
    achados = buscar_rua(G, "avenida", so_tomtom=True)
    assert [(t.u, t.v, t.chave) for t in achados] == [(2, 3, 0)]


def test_grafo_vazio():
    G = nx.MultiDiGraph()
    assert list(trechos(G)) == []
    assert buscar_rua(G, "x") == []
    assert agrupar_por_rua(G) == {}


def test_agrupar_por_rua():
    g = agrupar_por_rua(grafo_misto())
    assert set(g) == {"Rua Jose", "Avenida Padre José Nilson", "Avenida Dedé"}
    assert all(t.nomes for ts in g.values() for t in ts)
    assert [t.chave for t in g["Avenida Padre José Nilson"]] == [0]


def test_grafo_nao_e_mutado():
    G = grafo_misto()
    antes = [(u, v, k, dict(d)) for u, v, k, d in G.edges(keys=True, data=True)]
    nos = dict(G.nodes(data=True))
    list(trechos(G)); buscar_rua(G, "rua"); agrupar_por_rua(G, True)
    depois = [(u, v, k, dict(d)) for u, v, k, d in G.edges(keys=True, data=True)]
    assert antes == depois
    assert nos == dict(G.nodes(data=True))
    assert isinstance(G, nx.MultiDiGraph)


def test_ruas_sem_rede():
    fonte = open(ruas.__file__, encoding="utf-8").read()
    assert "requests" not in fonte and "tomtom_key" not in fonte
