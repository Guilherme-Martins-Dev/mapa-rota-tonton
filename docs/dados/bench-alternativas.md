Python 3.11.15, networkx 3.6.1, Windows 10; semente 42; peso `t_atual`.

Oráculo (força bruta, 7 vértices, paralelas, 200 sementes): 14 grafos sem caminho de 0 a 6 (nada a comparar); Yen igual à força bruta em 186/186 grafos com caminho.

| grade | vértices | arestas | menor_rota (ms) | Yen k=3 (ms) | Yen k=5 (ms) | Yen k=10 (ms) |
|---|---|---|---|---|---|---|
| 30x30 | 900 | 3480 | 12.6 | 1399 | 1729 | 3405 |
| 60x60 | 3600 | 14160 | 37.5 | 8280 | 15110 | 33127 |

Tempos: mediana de 5 execuções (menor_rota) ou 3 (Yen); origem e destino em cantos opostos.

| grade | custo ótima (s) | custo 2ª Yen (s) | sobreposição 2ª x ótima | custo 3ª Yen (s) | sobreposição 3ª x ótima |
|---|---|---|---|---|---|
| 30x30 | 383.4 | 383.8 | 96.4% | 384.0 | 90.6% |
| 60x60 | 762.1 | 762.6 | 88.0% | 762.6 | 98.2% |

Candidatos de Yen gerados até achar k rotas distintas (limite de 100; 'não achou' = só `aceitas` rotas em 100 candidatos). Uma execução cronometrada por linha.

| grade | k | max_sobreposicao | candidatos gerados | rotas aceitas | tempo (s) |
|---|---|---|---|---|---|
| 30x30 | 3 | 0.8 | 11 | 3 | 4.76 |
| 30x30 | 5 | 0.8 | 44 | 5 | 17.22 |
| 30x30 | 3 | 0.5 | 100 | 1 (não achou) | 44.47 |
| 60x60 | 3 | 0.8 | 64 | 3 | 242.01 |
| 60x60 | 5 | 0.8 | 100 | 3 (não achou) | 392.14 |
| 60x60 | 3 | 0.5 | 100 | 1 (não achou) | 394.80 |
