import osmnx as ox

LUGAR = "Messejana, Fortaleza, Ceará, Brazil"
G = ox.graph_from_place(LUGAR, network_type="drive") #grafo DIRIGIDO

print(f"Cruzamentos (vértices): {len(G.nodes)}")
print(f"Trechos de rua (arestas): {len(G.edges)}")

fig, ax = ox.plot_graph(G, node_size=6, node_color="#2a78d6",
                        edge_color="#898781", edge_linewidth=0.7, bgcolor="white")

# A "tabela de coordenadas": vértices e arestas viram tabelas
nodes, edges = ox.graph_to_gdfs(G)
print(nodes[["y", "x", "street_count"]].head()) #y= latitude, x = longitude
print(edges[["name", "length", "highway", "maxspeed"]].head())