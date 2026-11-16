import osmnx as ox

from tonton.config import LUGAR


def carregar_grafo(lugar: str = LUGAR):
    """Grafo viário DIRIGIDO (mão única) e MULTI (ruas paralelas): vértices = cruzamentos, arestas = trechos."""
    return ox.graph_from_place(lugar, network_type="drive")


def tabelas(G):
    """Tabela de vértices (y=latitude, x=longitude) e de arestas (nome, comprimento, highway, maxspeed)."""
    return ox.graph_to_gdfs(G)
