import networkx as nx
import pytest
from fastapi.testclient import TestClient

from tonton.api import criar_app
from tonton.planejador import preparar_grafo


def _grafo():
    G = nx.MultiDiGraph()
    pontos = {"a": (-38.500, -3.800), "b": (-38.480, -3.800), "c": (-38.460, -3.800)}
    for n, (x, y) in pontos.items():
        G.add_node(n, x=x, y=y)
    for u, v, nome in [("a", "b", "Rua Alfa"), ("b", "c", "Rua Beta"), ("c", "b", "Rua Beta"), ("b", "a", "Rua Alfa")]:
        G.add_edge(u, v, length=2000.0, maxspeed="50", name=nome)
    return preparar_grafo(G)


@pytest.fixture
def cliente():
    with TestClient(criar_app(_grafo())) as c:
        yield c


def test_rotas_por_nome_de_rua(cliente):
    r = cliente.get("/api/rotas", params={"origem": "Rua Alfa", "destino": "Rua Beta"})
    assert r.status_code == 200
    corpo = r.json()
    assert [f["properties"]["criterio"] for f in corpo["features"]] == ["distancia", "tempo", "consumo"]
    assert corpo["metadados"]["transito"] == "simulado"
    assert corpo["features"][0]["geometry"]["type"] == "LineString"


def test_rotas_por_coordenada(cliente):
    r = cliente.get("/api/rotas", params={"origem": "-3.8,-38.5", "destino": "-3.8,-38.46"})
    assert r.status_code == 200


def test_coordenada_fora_da_area(cliente):
    r = cliente.get("/api/rotas", params={"origem": "-3.5,-38.3", "destino": "-3.8,-38.46"})
    assert r.status_code == 422 and "fora da área" in r.json()["detail"]


def test_rua_inexistente(cliente):
    r = cliente.get("/api/rotas", params={"origem": "Rua Que Nao Existe", "destino": "Rua Beta"})
    assert r.status_code == 422 and "origem" in r.json()["detail"]


def test_origem_igual_destino(cliente):
    r = cliente.get("/api/rotas", params={"origem": "Rua Alfa", "destino": "Rua Alfa"})
    assert r.status_code == 422


def test_veiculo_desconhecido(cliente):
    r = cliente.get("/api/rotas", params={"origem": "Rua Alfa", "destino": "Rua Beta", "veiculo": "xyz"})
    assert r.status_code == 422


def test_veiculo_muda_os_litros(cliente):
    def litros(v):
        r = cliente.get("/api/rotas", params={"origem": "Rua Alfa", "destino": "Rua Beta", "veiculo": v})
        return r.json()["features"][0]["properties"]["litros"]

    assert litros("suv") > litros("golf-tdi")


def test_autocomplete_e_validacao(cliente):
    assert cliente.get("/api/ruas", params={"q": "alf"}).json() == ["Rua Alfa"]
    assert cliente.get("/api/ruas", params={"q": "a"}).status_code == 422


def test_catalogo(cliente):
    ids = {v["id"] for v in cliente.get("/api/veiculos").json()}
    assert {"popular", "golf-tdi"} <= ids
