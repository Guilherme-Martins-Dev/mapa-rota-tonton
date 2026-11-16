import osmnx as ox
import matplotlib.pyplot as plt

# Definir o local que deseja buscar
# Você pode alterar esta string para buscar outros bairros ou cidades
place_name = "Lagoinha"

print(f"Buscando dados de rede viária para: {place_name}...")

# Obter o grafo de ruas (drive especifica que queremos vias para carros)
# Se quiser todas as vias (incluindo pedestres), use network_type='all'
G = ox.graph_from_place(place_name, network_type='drive')

# Plotar a rede viária utilizando o próprio osmnx
fig, ax = ox.plot_graph(G, node_color='red', node_size=15, edge_color='#cccccc', edge_linewidth=1.5, show=False, close=False)
ax.set_title(f"Rede Viária - {place_name}", fontsize=14)
plt.show()

# Criando explicitamente as tabelas de vértices e arestas usando o grafo G
tabela_vertices, tabela_arestas = ox.graph_to_gdfs(G)

# Mostrar informações básicas
print(f"Quantidade de cruzamentos (vértices): {len(tabela_vertices)}")
print(f"Quantidade de trechos de rua (arestas): {len(tabela_arestas)}")

# Exibir as primeiras linhas (head) das tabelas
print("\nTabela de Vértices (Cruzamentos) - Primeiras linhas:")
print(tabela_vertices.head(5))

print("\nTabela de Arestas (Trechos de Rua) - Primeiras linhas:")
print(tabela_arestas.head(5))