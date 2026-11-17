# Benchmark do trânsito incremental

Medido com `scripts/bench_transito.py` em 2026-11-17. Python 3.11.15, networkx 3.6.1, requests 2.34.2, Windows 10, Intel64 Family 6 Model 142 Stepping 12, GenuineIntel; semente 42. Uma máquina, uma sessão: ordem de grandeza, não garantia.

## (a) CPU em grafo SINTÉTICO (não é Messejana)

Grafo sintético: 756 nós, 1881 arestas, 230 arestas TomTom em 224 pontos médios distintos. `consultar` falso e instantâneo (só CPU). Mediana de 30 execuções (recálculo/incremental) ou 20 (menor_rota); a cópia do grafo fica fora da medição.

| operação | tempo (ms) |
|---|---|
| recálculo COMPLETO (pesos + consumo, todas as arestas) | 15.78 |
| incremental, 5% dos pontos alterados (11 arestas reescritas) | 2.74 |
| incremental, 20% dos pontos alterados (46 arestas reescritas) | 2.89 |
| incremental, 100% dos pontos alterados (230 arestas reescritas) | 3.50 |

- `menor_rota` (t_atual), mediana entre 20 pares origem-destino alcançáveis (cada um: mediana de 5): 3.11 ms.
- `rota_continua_otima` (resultado de 5% alterados, rota de 45 arestas): 2.4 us (mediana de 200).

### Conferência de `rota_continua_otima` contra o Dijkstra

100 pares origem-destino alcançáveis por linha; em cada um, variação aleatória (pioram e melhoram) de uma fração dos pontos. `True` = a função diz que a rota segue ótima; `custo igual` = entre os `True`, o Dijkstra refeito deu o mesmo custo de uma rota (a rota antiga, reavaliada, custa o mesmo que a nova ótima, tolerância 1e-9). Esperado: sempre igual.

| peso | pontos alterados | True | False | True com custo igual (Dijkstra) |
|---|---|---|---|---|
| t_atual | 1% | 26 | 74 | 26 |
| t_atual | 5% | 0 | 100 | 0 |
| t_atual | 20% | 0 | 100 | 0 |
| litros | 1% | 26 | 74 | 26 |
| litros | 5% | 0 | 100 | 0 |
| litros | 20% | 0 | 100 | 0 |

## (b) Latência REAL da TomTom

8 pontos de Messejana em sequência, sem cache, `transito.consultar_trafego`. Resultados: ok, ok, ok, ok, ok, ok, ok, ok.

| consultas ok | mediana (ms) | mín (ms) | máx (ms) |
|---|---|---|---|
| 8 | 466 | 393 | 591 |

**EXTRAPOLAÇÃO** (não medida): refresh completo sequencial de 211 pontos = 211 x mediana = 98 s (faixa 83 a 125 s). Supõe latência constante, sem limite de taxa nem falhas, e que 8 pontos representam os 211.

