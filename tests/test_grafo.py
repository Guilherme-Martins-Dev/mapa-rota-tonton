import networkx as nx

from tonton import grafo


def test_carregar_grafo_chama_osmnx_com_rede_de_carros(monkeypatch):
    chamadas = []
    monkeypatch.setattr(
        grafo.ox, "graph_from_place",
        lambda lugar, network_type: chamadas.append((lugar, network_type)) or nx.MultiDiGraph(),
    )
    G = grafo.carregar_grafo("Qualquer Lugar")

    assert chamadas == [("Qualquer Lugar", "drive")]
    assert G.is_directed() and G.is_multigraph()
