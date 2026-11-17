---
name: quadro-modelagem
description: Regras de modelagem do quadro do professor (grafo dirigido e multi, dois pesos, t = comprimento/velocidade, Dijkstra com relaxamento). Use ao desenhar, implementar ou revisar qualquer etapa do back-end de rotas.
---

Fonte: `docs/quadro.png` (foto do quadro) e `analisar.md`.

## Modelagem
- **V = cruzamentos, E = trechos de rua.** O que sai da rede são coordenadas (lat, long): `y` = latitude, `x` = longitude nos vértices do osmnx.
- **Dirigido** = mão única. **Multi** = ruas paralelas. Em código: `MultiDiGraph` (`ox.graph_from_place(..., network_type="drive")`). Nunca converter para grafo simples sem escolher a aresta de menor peso.
- Tabelas: vértices (coordenadas) e arestas (nome da rua, comprimento, `highway`, `maxspeed`).

## Um grafo, dois pesos
- `t = comprimento / velocidade`. NUNCA velocidade / comprimento (o `analisar.md` escreve invertido; o quadro está certo).
- `t_livre` = via livre (usa `v_livre`); `t_atual` = trânsito agora (usa `v_atual`).
- Unidades: comprimento em metros, velocidade em km/h vinda da TomTom; converter para m/s (÷ 3,6) antes de dividir. Resultado em segundos.

## Algoritmo (Dijkstra = guloso + relaxamento)
- Relaxamento: `se d[u] + w(u,v) < d[v] então d[v] = d[u] + w(u,v)`.
- Caso do quadro para teste: dois caminhos até o mesmo vértice, com d[v] = 38 riscado e d[v] = 39 (o menor prevalece); arestas de pesos 4, 5 e 6 no desenho.
- Não enumerar todas as trajetórias (exponencial): o Dijkstra já dá a de menor custo. Em arestas paralelas usa-se a de menor peso.

## Rota e trânsito
- Origem → destino precisam existir na tabela (vértices); caso contrário, erro claro.
- Só ruas principais, secundárias, terciárias e `trunk` (~300 trechos) vão para a TomTom, por causa da cota. As demais usam velocidade de fallback.
- O trajeto começa a partir da próxima aresta (cruzamento); o ponto de consulta do trecho é o **ponto médio** da geometria.

## Pontos do quadro que NÃO estão claros (não implementar sem perguntar)
"1800 → mapa / rede social", "20:17", "Nautch anterior".
