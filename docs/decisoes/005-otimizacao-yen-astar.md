# 005. Otimização do Yen (Lawler + A*)

Status: aceita (2026-11-17).

## Contexto

O algoritmo de Yen (`rotas._yen`, decisão 002) gera as k menores rotas chamando um Dijkstra completo por candidato. Cada rota aceita gera até um candidato por vértice da rota anterior; cada candidato é um Dijkstra. O pior caso é O(k · n · (m + n) log n).

## Problema (número medido em Messejana)

Medido com `scripts/bench_otimizacao.py` no grafo real de Messejana (746 vértices, 1870 arestas, cache em disco), trânsito SIMULADO (`v_atual = v_livre × U[0,5; 1,0]` nas 228 arestas TomTom, semente fixa, TomTom não chamada), 50 pares sorteados com distância em linha reta > 2 km. Números completos em [dados/bench-otimizacao.md](../dados/bench-otimizacao.md).

Com o Yen original (antes desta etapa, commit 7484526), uma consulta de `menores_rotas(k=10, peso="t_atual")` custa, mediana / p90 / máx., **827,5 / 1452,7 / 1901,9 ms**; com `k=3`, 213,2 / 365,2 / 452,0 ms. Isso é lento demais para uma interação (planejador/CLI) com `k` moderado.

## Causa medida

1. **Cada chamada a `menor_rota` expande quase o grafo inteiro.** Sem heurística, o Dijkstra só para quando o destino sai da fila; mediana de **637 dos 746 vértices expandidos** por `menor_rota` (`t_atual`), máx. 734. O Yen chama um Dijkstra por desvio: mediana de 71/142/317 Dijkstras por consulta (k=3/5/10), com 262 a 280 vértices expandidos por Dijkstra.
2. **Uma pré-checagem cara, repetida a cada Dijkstra, que ninguém tinha suposto.** O código original de `dijkstra` validava o peso com `G.number_of_edges()` (soma os graus, O(V)) seguido de uma varredura de `G.edges(data=True)`. Essa checagem roda uma vez por Dijkstra, e o Yen chama Dijkstra centenas de vezes por consulta (até 317 em k=10). O cProfile de uma consulta típica (Yen original, k=3, `t_atual`, par de tempo mediano; tempo total sob o profile 848 ms) mostra essa pré-checagem dominando junto com a travessia de arestas paralelas:

   | função | chamadas | tempo próprio (ms) | % |
   |---|---|---|---|
   | `menor_peso_aresta` | 56328 | 154,9 | 18% |
   | `dijkstra` (próprio) | 80 | 97,1 | 11% |
   | `builtins.sum` | 119440 | 93,2 | 11% |
   | `reportviews.py:__iter__` | 59760 | 86,9 | 10% |
   | `reportviews.py:<genexpr>` | 208880 | 52,9 | 6% |
   | `_collections_abc:__iter__` | 112733 | 50,5 | 6% |
   | `coreviews.py:__getitem__` (×2) | 56502 | 31,0 + 29,3 | 4% + 3% |

   `builtins.sum`, `reportviews.py` e `coreviews.py` são a implementação do networkx por baixo de `G.number_of_edges()` e `G.edges(data=True)`: juntos, cerca de 33% do tempo do profile, só na pré-checagem, repetida sem necessidade a cada Dijkstra (o atributo de peso não muda entre eles, dentro da mesma consulta). `menor_peso_aresta` (18%) é a travessia das arestas paralelas em cada sucessor visitado, inerente ao multigrafo.

Esta pré-checagem já foi trocada, neste `rotas.py`, por uma versão que olha só a primeira aresta do grafo (e cai para a varredura completa somente se ela não tiver o atributo) — chamada de "D" no benchmark, presente mesmo com Lawler e A* desligados. Isso já responde por boa parte do ganho medido (ver tabela de candidatas): mediana 1,5x a 2,75x mais rápido que o original, dependendo do peso e do k, só com essa troca.

## Decisão

Interface (`src/tonton/rotas.py`):
- `dijkstra(..., *, ignorar_vertices=frozenset(), ignorar_arestas=frozenset(), heuristica=None)`: `heuristica` keyword-only; liga o A* (fila ordenada por `dist + h`; exige `destino`).
- `menores_rotas(G, origem, destino, k=3, peso="t_atual", *, otimizar=True)` e `rotas_alternativas(..., *, otimizar=True)`: `otimizar=True` (padrão) liga Lawler + A*; `otimizar=False` é o Yen original (mesmo algoritmo, mesma ordem de desvios).
- `heuristica_haversine(G, destino, peso)`: monta h(v) = c × haversine(v, destino) varrendo as arestas (O(E)), uma vez por chamada de `menores_rotas`/`rotas_alternativas` (não por Dijkstra, não guardada no grafo).
- `_yen(..., *, lawler=False, astar=False, poda_k=None)`: função interna; `menores_rotas`/`rotas_alternativas` ligam `lawler` e `astar` juntos via `otimizar`. `poda_k` existe na função interna mas **não é exposto** pela API pública (ver candidata C, rejeitada).

**Candidatas aceitas** (medidas isoladamente e em conjunto; custos idênticos ao original em todos os casos, ver Evidência):
- **A — modificação de Lawler:** cada candidata guarda o índice do vértice de desvio da rota-pai; ao aceitá-la, só os desvios a partir desse índice são recalculados. Reduz o número de Dijkstras por consulta de forma mensurável: por exemplo, para `t_atual`, k=10, de 317 (original/D) para 174 (A+D) Dijkstras (mediana).
- **B — A* com heurística haversine:** h(v) = r_min × haversine(v, destino), `r_min` = menor razão peso/length entre as arestas, escalado por min(1, menor length/haversine(u,v)) para segurança em grafos sintéticos (ver prova na pergunta 5 do FAQ). Reduz vértices expandidos por Dijkstra sem reduzir o número de Dijkstras isoladamente (por exemplo t_atual k=10: 317 Dijkstras tanto em D quanto em B+D, mas 83562 → 49626 vértices expandidos, mediana).
- **A+B juntas** dão o maior ganho medido: para `t_atual`, k=10, mediana 827,5 ms (original) → 147,8 ms (A+B+D), **5,60x**; para `length`, k=10, mediana 916,5 ms → 53,6 ms, **17,09x** (length é o peso onde a heurística é mais apertada: r_min = 1, h = a própria haversine). Tabela completa por peso e k em [dados/bench-otimizacao.md](../dados/bench-otimizacao.md).

**Candidata rejeitada:**
- **C — poda de spurs por `custo_raiz + h(desvio) >= corte`:** medida isoladamente sobre A+B (variante "A+B+C+D"). Para o peso `t_atual`, o número de Dijkstras e de vértices expandidos (mediana, k=3/5/10) é **idêntico** entre A+B+D e A+B+C+D (52/91/174 Dijkstras; 7568/11169/19890 vértices expandidos): a poda não cortou nenhum desvio nesses testes, ou seja, `corte` nunca ficou apertado o bastante. Os tempos (que incluem o custo de calcular `corte` e `heuristica(desvio)` extra por desvio) oscilaram para os dois lados dentro do ruído de medição (uma amostra por par, sem repetição): por exemplo, `length` k=3 piorou de 30,2 ms (A+B+D) para 46,1 ms (A+B+C+D), **34% mais lento**; `litros` k=10 melhorou de 102,7 ms para 75,8 ms. Sem redução de trabalho medida e com piora em vários casos, **C fica fora da API pública** (o parâmetro `poda_k` existe em `_yen` mas não é ligado por `menores_rotas`/`rotas_alternativas`).

## Alternativas descartadas

- **Dijkstra bidirecional:** reduziria os vértices expandidos buscando da origem e do destino ao mesmo tempo, mas exige grafo reverso (sucessores do destino = antecessores) e uma condição de parada mais delicada (quando as duas buscas "se encontram", não é só a soma dos dois `dist`); no multigrafo com arestas paralelas e `ignorar_vertices`/`ignorar_arestas` do Yen, a implementação e os testes de corretude ficam mais complexos. A* com a heurística medida já cobre o ganho que se buscava aqui; não implementado, não medido.
- **ALT (A*, Landmarks, Triangle inequality) / landmarks:** dá heurísticas melhores que a haversine pura, mas exige pré-processar e guardar distâncias a landmarks no grafo — o trânsito incremental (decisão 003) muda pesos entre atualizações, e uma heurística pré-calculada por landmarks ficaria defasada (o mesmo problema que levou a recalcular `heuristica_haversine` a cada chamada, nunca guardá-la). Não implementado, não medido.
- **Contraction hierarchies:** pré-processamento caro (ordem de contração, atalhos) pensado para grafos estáticos consultados muitas vezes; aqui o grafo muda com o trânsito a cada ciclo de atualização (decisão 003), o que invalidaria o pré-processamento com frequência. Não implementado, não medido.
- **Árvore reversa (do destino) para podar spurs:** calcularia de uma vez só as distâncias do destino a todos os vértices (Dijkstra no grafo reverso) e usaria isso para podar ou até substituir o cálculo de cada desvio. É mais forte que a heurística haversine (seria o h "perfeito"), mas exigiria manter o grafo reverso e repetir esse Dijkstra a cada consulta (pesos mudam com o trânsito); a candidata C (poda por heurística, mais simples) já não mostrou corte algum no grafo medido, o que não dá evidência de que a poda por árvore reversa pagasse o custo do Dijkstra extra. Não implementado, não medido.
- **Paralelizar os spurs (desvios) de uma mesma rodada:** cada desvio é um Dijkstra independente; threads poderiam calculá-los em paralelo. O GIL do Python exigiria `multiprocessing` (custo de serializar o grafo ou usar memória compartilhada) ou reescrever o Dijkstra em código nativo; nenhuma das duas foi medida, e a simplicidade pedida pela regra do projeto (otimizar só com causa medida) não justifica esse salto sem medir o custo de IPC primeiro. Não implementado, não medido.

## Consequências

- **A* exige heurística admissível e consistente.** A nossa (haversine escalada por `r_min` e pela razão length/haversine) é consistente por construção (prova na pergunta 5 do FAQ); se o peso tiver alguma aresta sem `length` e sem razão calculável de forma segura, `heuristica_haversine` devolve `None` e o código cai de volta ao Dijkstra puro (sem erro, sem risco de heurística inconsistente).
- **A heurística é recalculada a cada chamada de `menores_rotas`/`rotas_alternativas`, nunca guardada no grafo**, por causa do trânsito incremental (decisão 003): `atualizar_transito` pode aumentar uma velocidade entre duas consultas, o que tornaria um `r_min` guardado grande demais e quebraria a consistência.
- **Custo extra de O(E) por consulta** (não por Dijkstra) para montar a heurística: medido em 9,28 ms (mediana de 15 chamadas) no grafo de Messejana — pequeno frente aos cento(s) de ms que o Yen economiza a partir de k=3.
- **`otimizar=False` preserva o comportamento antigo** (mesmo algoritmo, mesma ordem de geração dos candidatos) para quem precisar comparar ou depurar; é também o que o benchmark usa como referência.
- **`poda_k` existe mas não está ligado**: fica disponível para quem quiser medir de novo em outro grafo ou faixa de k, mas não é exercitado pelos testes nem pela API pública.

## Evidência

Medido com `scripts/bench_otimizacao.py`, grafo real de Messejana (cache em disco), trânsito simulado, semente 42. Ambiente e tabelas completas (tempos por peso/k, contagens de Dijkstra e vértices expandidos, cProfile, verificação de custos em 450 + 150 comparações em Messejana e 2760 em 200 grafos aleatórios pequenos — 0 divergências em todas) em [dados/bench-otimizacao.md](../dados/bench-otimizacao.md). Teoria (admissibilidade, consistência, por que a heurística é segura) em [aula/faq-otimizacao.md](../aula/faq-otimizacao.md).
