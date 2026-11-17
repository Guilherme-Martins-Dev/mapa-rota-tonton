Data 2026-11-17; Python 3.11.15, networkx 3.6.1, osmnx 2.1.2; Windows-10-10.0.19045-SP0, Intel64 Family 6 Model 142 Stepping 12, GenuineIntel, 8 CPUs lógicas; semente 42.
Grafo REAL de Messejana (cache em disco, fonte `api-osm`): 746 vértices, 1870 arestas. Trânsito SIMULADO (v_atual = v_livre x U[0,5; 1,0] em 228 arestas TomTom); a TomTom não foi chamada. 50 pares sorteados na maior componente fortemente conexa (737 vértices), distância em linha reta > 2000 m.

## Passo 0: tempos (ms) por consulta, nos 50 pares (mediana / p90 / máx.), Yen original

| peso | menor_rota | Yen k=3 | Yen k=5 | Yen k=10 |
|---|---|---|---|---|
| length | 7.1 / 9.2 / 10.5 | 202.5 / 412.5 / 586.0 | 387.5 / 653.6 / 1065.6 | 916.5 / 1469.4 / 2309.8 |
| t_atual | 4.5 / 5.9 / 7.0 | 213.2 / 365.2 / 452.0 | 398.6 / 701.3 / 798.5 | 827.5 / 1452.7 / 1901.9 |
| litros | 4.9 / 5.7 / 6.2 | 205.0 / 368.2 / 599.7 | 363.4 / 723.9 / 912.8 | 754.0 / 1372.8 / 1923.1 |

## Passo 0: nº de Dijkstras e de vértices expandidos por consulta do Yen original (mediana / máx. nos 50 pares)

Expandido = vértice cujos sucessores foram percorridos (contado por um wrapper em `G.successors`, fora do código de produção).

| peso | k | Dijkstras | vértices expandidos | expandidos por Dijkstra |
|---|---|---|---|---|
| length | 3 | 71 / 101 | 18684 / 34595 | 276 |
| length | 5 | 142 / 202 | 38048 / 68089 | 280 |
| length | 10 | 323 / 449 | 86182 / 151050 | 275 |
| t_atual | 3 | 71 / 104 | 19136 / 35012 | 274 |
| t_atual | 5 | 142 / 205 | 37827 / 67122 | 270 |
| t_atual | 10 | 317 / 462 | 83562 / 146411 | 262 |
| litros | 3 | 71 / 102 | 19109 / 34631 | 272 |
| litros | 5 | 142 / 203 | 37599 / 68212 | 267 |
| litros | 10 | 319 / 456 | 84474 / 151187 | 262 |

Um `menor_rota` (t_atual) expande, em mediana, 637 dos 746 vértices (máx. 734).

## Passo 0: cProfile de uma consulta típica (Yen original, k=3, t_atual, par de tempo mediano)

Tempo total sob o profile: 848 ms (o cProfile infla o tempo; vale a proporção). Ordenado por tempo próprio (tottime).

| função | chamadas | tempo próprio (ms) | % |
|---|---|---|---|
| `rotas_original.py:menor_peso_aresta` | 56328 | 154.9 | 18% |
| `rotas_original.py:dijkstra` | 80 | 97.1 | 11% |
| `~:<built-in method builtins.sum>` | 119440 | 93.2 | 11% |
| `reportviews.py:__iter__` | 59760 | 86.9 | 10% |
| `reportviews.py:<genexpr>` | 208880 | 52.9 | 6% |
| `<frozen _collections_abc>:__iter__` | 112733 | 50.5 | 6% |
| `coreviews.py:__getitem__` | 56502 | 31.0 | 4% |
| `coreviews.py:__getitem__` | 56502 | 29.3 | 3% |

## Passo 1: candidatas isoladas, tempo em ms por consulta (mediana / p90 / máx.) e speedup da mediana sobre o original

| peso | k | original | D | A+D | B+D | A+B+D | A+B+C+D |
|---|---|---|---|---|---|---|---|
| length | 3 | 202.5 / 412.5 / 586.0 | 123.5 / 217.2 / 394.3 (1.64x) | 77.5 / 196.9 / 317.9 (2.61x; 1.59x sobre D) | 36.8 / 52.8 / 67.9 (5.51x; 3.36x sobre D) | 30.2 / 65.0 / 115.2 (6.71x; 4.09x sobre D) | 46.1 / 73.7 / 86.3 (4.39x; 2.68x sobre D) |
| length | 5 | 387.5 / 653.6 / 1065.6 | 219.7 / 443.8 / 642.1 (1.76x) | 115.1 / 203.1 / 309.3 (3.37x; 1.91x sobre D) | 87.7 / 144.9 / 266.6 (4.42x; 2.50x sobre D) | 40.1 / 112.8 / 172.3 (9.67x; 5.48x sobre D) | 47.7 / 79.4 / 124.6 (8.13x; 4.61x sobre D) |
| length | 10 | 916.5 / 1469.4 / 2309.8 | 507.5 / 960.1 / 1310.5 (1.81x) | 205.8 / 357.1 / 748.6 (4.45x; 2.47x sobre D) | 156.5 / 384.0 / 533.9 (5.86x; 3.24x sobre D) | 53.6 / 98.3 / 118.1 (17.09x; 9.47x sobre D) | 76.6 / 139.9 / 253.2 (11.96x; 6.62x sobre D) |
| t_atual | 3 | 213.2 / 365.2 / 452.0 | 121.7 / 222.2 / 273.5 (1.75x) | 78.6 / 130.8 / 214.1 (2.71x; 1.55x sobre D) | 78.4 / 161.2 / 295.3 (2.72x; 1.55x sobre D) | 51.8 / 86.3 / 117.1 (4.11x; 2.35x sobre D) | 58.9 / 142.0 / 227.3 (3.62x; 2.06x sobre D) |
| t_atual | 5 | 398.6 / 701.3 / 798.5 | 242.5 / 442.3 / 556.3 (1.64x) | 112.4 / 240.0 / 476.0 (3.55x; 2.16x sobre D) | 137.9 / 292.2 / 371.6 (2.89x; 1.76x sobre D) | 87.4 / 193.1 / 296.6 (4.56x; 2.77x sobre D) | 71.6 / 114.0 / 156.8 (5.57x; 3.39x sobre D) |
| t_atual | 10 | 827.5 / 1452.7 / 1901.9 | 512.4 / 948.4 / 1226.8 (1.61x) | 192.1 / 548.3 / 771.5 (4.31x; 2.67x sobre D) | 329.2 / 538.7 / 846.0 (2.51x; 1.56x sobre D) | 147.8 / 339.0 / 449.7 (5.60x; 3.47x sobre D) | 136.0 / 226.9 / 464.5 (6.09x; 3.77x sobre D) |
| litros | 3 | 205.0 / 368.2 / 599.7 | 119.5 / 235.8 / 288.5 (1.72x) | 70.3 / 110.4 / 144.5 (2.92x; 1.70x sobre D) | 69.3 / 133.0 / 163.8 (2.96x; 1.72x sobre D) | 36.7 / 53.6 / 68.5 (5.59x; 3.26x sobre D) | 39.0 / 75.1 / 116.9 (5.26x; 3.06x sobre D) |
| litros | 5 | 363.4 / 723.9 / 912.8 | 217.4 / 438.0 / 785.3 (1.67x) | 112.3 / 248.6 / 594.7 (3.24x; 1.94x sobre D) | 107.7 / 222.7 / 273.1 (3.37x; 2.02x sobre D) | 51.8 / 78.0 / 119.5 (7.02x; 4.20x sobre D) | 63.5 / 134.2 / 258.9 (5.73x; 3.43x sobre D) |
| litros | 10 | 754.0 / 1372.8 / 1923.1 | 491.4 / 912.7 / 1455.3 (1.53x) | 217.5 / 377.8 / 572.6 (3.47x; 2.26x sobre D) | 225.0 / 390.6 / 740.3 (3.35x; 2.18x sobre D) | 102.7 / 207.8 / 399.1 (7.34x; 4.79x sobre D) | 75.8 / 135.5 / 243.6 (9.94x; 6.48x sobre D) |

`menor_rota` (k=1), mediana / p90 / máx. em ms: Dijkstra original, Dijkstra atual (D) e A* (inclui montar a heurística, que varre as arestas):

| peso | original | D | A*+D |
|---|---|---|---|
| length | 7.1 / 9.2 / 10.5 | 3.3 / 3.8 / 4.4 (2.13x) | 5.8 / 7.0 / 8.8 (1.22x) |
| t_atual | 4.5 / 5.9 / 7.0 | 3.7 / 4.1 / 4.3 (1.21x) | 7.9 / 8.9 / 9.5 (0.56x) |
| litros | 4.9 / 5.7 / 6.2 | 7.3 / 8.2 / 8.6 (0.68x) | 7.2 / 15.9 / 16.9 (0.68x) |

Custo de montar a heurística (varredura O(E) + coordenadas), mediana de 15 chamadas: 9.28 ms.

Dijkstras e vértices expandidos por consulta (t_atual, mediana nos 50 pares):

| k | variante | Dijkstras | vértices expandidos |
|---|---|---|---|
| 3 | original | 71 | 19136 |
| 3 | D | 71 | 19136 |
| 3 | A+D | 52 | 13336 |
| 3 | B+D | 71 | 11958 |
| 3 | A+B+D | 52 | 7568 |
| 3 | A+B+C+D | 52 | 7568 |
| 5 | original | 142 | 37827 |
| 5 | D | 142 | 37827 |
| 5 | A+D | 91 | 19374 |
| 5 | B+D | 142 | 22715 |
| 5 | A+B+D | 91 | 11169 |
| 5 | A+B+C+D | 91 | 11169 |
| 10 | original | 317 | 83562 |
| 10 | D | 317 | 83562 |
| 10 | A+D | 174 | 34099 |
| 10 | B+D | 317 | 49626 |
| 10 | A+B+D | 174 | 19890 |
| 10 | A+B+C+D | 174 | 19890 |

## Passo 2: verificação (custos das k rotas, tolerância 1e-9 relativa)

| variante | comparações (par x peso x k) | divergências |
|---|---|---|
| D | 450 | 0 |
| A+D | 450 | 0 |
| B+D | 450 | 0 |
| A+B+D | 450 | 0 |
| A+B+C+D | 450 | 0 |

API pública `menores_rotas(k=5)`, otimizar=True x False: 150 comparações (par x peso), 0 divergências.

Grafos aleatórios pequenos (6 a 12 vértices, com coordenadas, paralelas e 5% de arestas com length 0): 200 grafos, 101 com `length` MENOR que a distância das coordenadas; 48 (grafo, peso) sem caminho (nada a comparar); 2760 comparações (grafo x peso x variante, k=6): 0 divergências.

