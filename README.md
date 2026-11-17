# mapa-rota-tonton

Rotas em Messejana (Fortaleza). As ruas viram um grafo (OpenStreetMap via `osmnx`), a TomTom informa o trânsito
e o Dijkstra escolhe a rota por **menor distância**, **menor tempo** ou **menor consumo de combustível**.

Modelagem (ver [docs/quadro.png](docs/quadro.png) e [analisar.md](analisar.md)):

- vértices = cruzamentos, arestas = trechos de rua; grafo **dirigido** (mão única) e **multi** (ruas paralelas)
- um grafo, dois pesos: `t_livre` e `t_atual`, com `t = comprimento / velocidade`
- Dijkstra = guloso com relaxamento: `se d[u] + w(u,v) < d[v] então d[v] = d[u] + w(u,v)`

## Rodando

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
copy .env.example .env   # preencha TOMTOM_KEY
.\.venv\Scripts\python.exe -m pytest
```

## Usando a CLI

```powershell
.\.venv\Scripts\python.exe -m tonton --origem "-3.8267,-38.4935" --destino "Avenida Dedé Brasil" --criterio todos --geojson rotas.geojson --mostrar
```

- `--origem` / `--destino`: `"lat,lon"` ou nome de rua.
- `--criterio distancia|tempo|consumo|todos` (padrão `todos`): imprime km, min e litros de cada rota, com `*` no melhor de cada coluna.
- `--geojson ARQUIVO`: grava as rotas (FeatureCollection de LineString `[lon, lat]`).
- `--mostrar`: desenha as rotas no mapa.
- `--sem-transito`: não usa a TomTom (velocidades do OSM). Sem isso é preciso `TOMTOM_KEY` no ambiente ou no `.env`.

## Etapas (um PR por etapa)

| Etapa | Conteúdo |
|---|---|
| 0 | estrutura, git, CI |
| 1 | identificar ruas: trecho, ponto médio, cruzamento seguinte |
| 2 | pesos de tempo (`t_livre`, `t_atual`) com TomTom |
| 3 | Dijkstra: menor tempo |
| 4 | menor consumo de combustível |
| 5 | planejador: escolhe distância / tempo / consumo (CLI e GeoJSON) |

A interface gráfica vem depois do back-end.
