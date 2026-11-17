"""Compara o grafo baixado pelo Overpass com o baixado pela API do OSM, no mesmo momento. NÃO roda no CI.

Uso: ./.venv/Scripts/python.exe scripts/comparar_fontes.py
Só funciona se o Overpass responder (se não, o script termina com o erro dele). Faz um download de cada fonte
(cerca de 85 s e 50 s em Messejana) e nada é gravado em disco.
"""
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

import networkx as nx
import osmnx as ox

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # roda sem instalar o pacote

from tonton.config import LUGAR  # noqa: E402
from tonton.grafo import baixar_via_api_osm  # noqa: E402


def resumo(G, rotulo):
    comp = list(nx.strongly_connected_components(G))
    L = [float(d["length"]) for *_, d in G.edges(keys=True, data=True)]
    print(f"{rotulo}: {len(G)} vértices, {G.number_of_edges()} arestas, soma length {sum(L) / 1000:.3f} km, "
          f"mediana {statistics.median(L):.2f} m, {len(comp)} componentes fortes (maior {max(map(len, comp))})")


def igual(campo, a, b):
    if campo == "length":
        return abs(float(a) - float(b)) < 1e-6
    if campo == "geometry":
        return (a is None and b is None) or (a is not None and b is not None and a.equals_exact(b, 1e-9))
    return a == b


def main():
    ox.settings.use_cache = False
    t0 = time.perf_counter()
    G_o = ox.graph_from_place(LUGAR, network_type="drive")
    t1 = time.perf_counter()
    G_a = baixar_via_api_osm(LUGAR)
    t2 = time.perf_counter()
    print(f"download Overpass {t1 - t0:.1f} s; API do OSM {t2 - t1:.1f} s")
    resumo(G_o, "overpass")
    resumo(G_a, "api-osm ")
    print(f"nós: só no Overpass {len(set(G_o) - set(G_a))}, só na API {len(set(G_a) - set(G_o))}")
    ko, ka = set(G_o.edges(keys=True)), set(G_a.edges(keys=True))
    print(f"atributos de aresta: Overpass {sorted({c for *_, d in G_o.edges(keys=True, data=True) for c in d})}")
    print(f"atributos de aresta: API      {sorted({c for *_, d in G_a.edges(keys=True, data=True) for c in d})}")
    print(f"edges(keys=True): só no Overpass {len(ko - ka)}, só na API {len(ka - ko)}, em comum {len(ko & ka)}")
    dif = Counter()
    for u, v, k in ko & ka:
        a, b = G_o.edges[u, v, k], G_a.edges[u, v, k]
        dif.update(c for c in a.keys() | b.keys() if not igual(c, a.get(c), b.get(c)))
    print(f"arestas em comum, diferenças por atributo (todos os atributos das duas): {dict(dif) or 'nenhuma'}")
    dn = Counter()
    for n in set(G_o) & set(G_a):
        a, b = G_o.nodes[n], G_a.nodes[n]
        dn.update(c for c in a.keys() | b.keys() if a.get(c) != b.get(c))
    print(f"nós em comum, diferenças por atributo (todos): {dict(dn) or 'nenhuma'}")


if __name__ == "__main__":
    main()
