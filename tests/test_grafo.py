import os
import time

import networkx as nx
import osmnx as ox
import pytest
from shapely.geometry import LineString

from tonton import grafo, pesos, ruas

LUGAR = "Messejana, Fortaleza, Ceará"


def test_carregar_grafo_chama_osmnx_com_rede_de_carros(monkeypatch, tmp_path):
    chamadas = []
    monkeypatch.setattr(
        grafo.ox, "graph_from_place",
        lambda lugar, network_type: chamadas.append((lugar, network_type)) or nx.MultiDiGraph(),
    )
    G = grafo.carregar_grafo("Qualquer Lugar", pasta=tmp_path)

    assert chamadas == [("Qualquer Lugar", "drive")]
    assert G.is_directed() and G.is_multigraph()


# ---------------------------------------------------------------- cache em disco
def _bruto():
    """Grafo sintético no formato do OSM: mão única, paralelas, name ausente/lista, highway lista."""
    G = nx.MultiDiGraph(crs="EPSG:4326")
    G.add_node(1, x=-38.500, y=-3.800)
    G.add_node(2, x=-38.490, y=-3.800)
    G.add_node(3, x=-38.490, y=-3.810)
    G.add_edge(1, 2, osmid=10, length=1000.0, highway="primary", name="Avenida Rapida", maxspeed="60",
               oneway=True, reversed=False,
               geometry=LineString([(-38.500, -3.800), (-38.495, -3.7995), (-38.490, -3.800)]))
    G.add_edge(1, 2, osmid=11, length=1500.0, highway=["secondary", "tertiary"], name=["Rua A", "Rua B"],
               maxspeed=["40", "50"], oneway=True, reversed=False)
    G.add_edge(2, 3, osmid=12, length=800.0, highway="residential", oneway=True, reversed=False)
    return G


@pytest.fixture
def baixador(monkeypatch):
    chamadas = []

    def falso(lugar, network_type):
        chamadas.append((lugar, network_type))
        return _bruto()

    monkeypatch.setattr(grafo.ox, "graph_from_place", falso)
    return chamadas


def _envelhecer(caminho, dias):
    t = time.time() - dias * 86400
    os.utime(caminho, (t, t))


def _arestas(G):
    return sorted(G.edges(keys=True))


def _aresta(G, osmid):
    return next(d for _, _, d in G.edges(data=True) if d["osmid"] == osmid)


def test_slug_remove_acentos_espacos_virgulas_e_maiusculas():
    assert grafo.slug(LUGAR) == "messejana-fortaleza-ceara"
    assert grafo.slug("  São José,  Ñandú!! ") == "sao-jose-nandu"


def test_arquivo_cache_usa_pasta_e_slug(tmp_path):
    assert grafo.arquivo_cache(LUGAR, tmp_path) == tmp_path / "grafo-messejana-fortaleza-ceara.graphml"


def test_sem_arquivo_baixa_e_grava(baixador, tmp_path):
    G = grafo.carregar_grafo(LUGAR, pasta=tmp_path)

    assert baixador == [(LUGAR, "drive")]
    assert grafo.arquivo_cache(LUGAR, tmp_path).is_file()
    assert [p.name for p in tmp_path.iterdir()] == ["grafo-messejana-fortaleza-ceara.graphml"]  # sem .tmp
    assert G.number_of_edges() == 3


def test_cria_a_pasta_do_cache_se_nao_existir(baixador, tmp_path):
    pasta = tmp_path / "a" / "b"
    grafo.carregar_grafo(LUGAR, pasta=pasta)
    assert grafo.arquivo_cache(LUGAR, pasta).is_file()


def test_arquivo_valido_nao_baixa_e_devolve_grafo_equivalente(baixador, tmp_path):
    original = grafo.carregar_grafo(LUGAR, pasta=tmp_path)
    baixador.clear()

    lido = grafo.carregar_grafo(LUGAR, pasta=tmp_path)

    assert baixador == []
    assert lido.is_directed() and lido.is_multigraph()
    assert _arestas(lido) == _arestas(original)
    assert set(lido.nodes) == set(original.nodes)


def test_arquivo_expirado_baixa_de_novo(baixador, tmp_path):
    grafo.carregar_grafo(LUGAR, pasta=tmp_path)
    caminho = grafo.arquivo_cache(LUGAR, tmp_path)
    _envelhecer(caminho, 31)

    grafo.carregar_grafo(LUGAR, validade_dias=30, pasta=tmp_path)

    assert len(baixador) == 2
    assert time.time() - caminho.stat().st_mtime < 3600  # regravado


def test_arquivo_dentro_da_validade_nao_baixa(baixador, tmp_path):
    grafo.carregar_grafo(LUGAR, pasta=tmp_path)
    _envelhecer(grafo.arquivo_cache(LUGAR, tmp_path), 29)

    grafo.carregar_grafo(LUGAR, validade_dias=30, pasta=tmp_path)

    assert len(baixador) == 1


def test_arquivo_corrompido_baixa_de_novo_e_regrava(baixador, tmp_path):
    caminho = grafo.arquivo_cache(LUGAR, tmp_path)
    caminho.write_bytes(b"\x00\xffisto nao e graphml\x01")

    G = grafo.carregar_grafo(LUGAR, pasta=tmp_path)

    assert len(baixador) == 1
    assert G.number_of_edges() == 3
    assert ox.load_graphml(caminho).number_of_edges() == 3  # agora e valido


def test_usar_cache_false_baixa_mesmo_com_arquivo_valido_e_regrava(baixador, tmp_path):
    grafo.carregar_grafo(LUGAR, pasta=tmp_path)
    caminho = grafo.arquivo_cache(LUGAR, tmp_path)
    _envelhecer(caminho, 20)
    antes = caminho.stat().st_mtime

    grafo.carregar_grafo(LUGAR, usar_cache=False, pasta=tmp_path)

    assert len(baixador) == 2
    assert caminho.stat().st_mtime > antes


def test_ida_e_volta_preserva_tipos_do_projeto(baixador, tmp_path):
    grafo.carregar_grafo(LUGAR, pasta=tmp_path)
    baixador.clear()
    G = grafo.carregar_grafo(LUGAR, pasta=tmp_path)
    assert baixador == []

    rapida, dupla = _aresta(G, 10), _aresta(G, 11)
    assert isinstance(rapida["length"], float) and rapida["length"] == 1000.0
    assert isinstance(rapida["geometry"], LineString)
    assert rapida["highway"] == "primary" and rapida["name"] == "Avenida Rapida"
    assert rapida["maxspeed"] == "60"
    assert dupla["highway"] == ["secondary", "tertiary"]
    assert dupla["name"] == ["Rua A", "Rua B"]
    assert dupla["maxspeed"] == ["40", "50"]
    assert isinstance(G.nodes[1]["x"], float) and isinstance(G.nodes[1]["y"], float)


def test_grafo_lido_do_cache_funciona_em_trechos_e_pesos(baixador, tmp_path):
    grafo.carregar_grafo(LUGAR, pasta=tmp_path)
    G = grafo.carregar_grafo(LUGAR, pasta=tmp_path)

    lista = list(ruas.trechos(G))
    assert len(lista) == 3
    assert any(t.nomes == ("Rua A", "Rua B") for t in lista)
    assert any(t.nomes == () for t in lista)  # via sem name

    pesos.atribuir_pesos(G)
    for _, _, d in G.edges(data=True):
        assert d["t_livre"] > 0 and d["t_atual"] == d["t_livre"]
    assert _aresta(G, 10)["t_livre"] == pytest.approx(1000.0 / (60 / 3.6))


def test_pesos_nao_sao_gravados_no_cache(baixador, tmp_path):
    G = grafo.carregar_grafo(LUGAR, pasta=tmp_path)
    pesos.atribuir_pesos(G)  # preparar depois de gravar
    assert "t_livre" in next(iter(G.edges(data=True)))[2]

    for G2 in (ox.load_graphml(grafo.arquivo_cache(LUGAR, tmp_path)),
               grafo.carregar_grafo(LUGAR, pasta=tmp_path)):
        for _, _, d in G2.edges(data=True):
            assert not {"t_livre", "t_atual", "v_livre", "v_atual", "litros"} & d.keys()


def test_falha_de_escrita_nao_deixa_graphml_parcial(baixador, monkeypatch, tmp_path):
    def quebra(G, caminho, *a, **k):
        with open(caminho, "w") as f:
            f.write("<graphml>parcial")
        raise OSError("disco cheio")

    monkeypatch.setattr(grafo.ox, "save_graphml", quebra)

    with pytest.raises(OSError):
        grafo.carregar_grafo(LUGAR, pasta=tmp_path)

    assert not grafo.arquivo_cache(LUGAR, tmp_path).exists()
    assert list(tmp_path.iterdir()) == []  # nem .tmp sobra


def test_arquivo_cache_nunca_sai_da_pasta(tmp_path):
    for nome in ("../x", "a/b.c", "..\\..\\y", "/etc/passwd"):
        assert grafo.arquivo_cache(nome, tmp_path).parent == tmp_path


def test_falha_de_escrita_preserva_cache_antigo(baixador, monkeypatch, tmp_path):
    grafo.carregar_grafo(LUGAR, pasta=tmp_path)
    caminho = grafo.arquivo_cache(LUGAR, tmp_path)
    antigo = caminho.read_bytes()

    def quebra(G, destino, *a, **k):
        with open(destino, "w") as f:
            f.write("lixo")
        raise OSError("disco cheio")

    monkeypatch.setattr(grafo.ox, "save_graphml", quebra)
    with pytest.raises(OSError):
        grafo.carregar_grafo(LUGAR, usar_cache=False, pasta=tmp_path)

    assert caminho.read_bytes() == antigo
