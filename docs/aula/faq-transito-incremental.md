# FAQ: trânsito incremental

Perguntas que um professor de grafos faria sobre a atualização incremental. Contexto completo em [decisoes/003-transito-incremental.md](../decisoes/003-transito-incremental.md); números em [dados/bench-transito.md](../dados/bench-transito.md) (CPU em grafo sintético, não Messejana; latência da TomTom real, 8 consultas).

**1. Por que não recalcular tudo a cada ciclo?**
Porque o custo não está no cálculo. Medido: recálculo completo de pesos e consumo em ~16 ms (grafo sintético de porte parecido), `menor_rota` em ~3 ms, e cada consulta real à TomTom com mediana de 466 ms. Refazer tudo significa 211 consultas (extrapolado: ~98 s, não medido) e gasto de cota, para atualizar trechos que quase não mudaram.

**2. O que garante que a rota continua ótima quando só piorou fora dela?**
Monotonicidade. Se a rota R era ótima com custo C, qualquer outra rota custava pelo menos C. Se nenhuma aresta de R mudou, R ainda custa C; as outras só tiveram arestas que pioraram ou ficaram iguais (pesos não negativos), então custam pelo menos o que custavam, logo pelo menos C. R segue ótima, possivelmente empatada.

**3. E se uma aresta fora da rota melhorou?**
Aí não há garantia: ela pode ter criado um atalho melhor que R. `rota_continua_otima` devolve `False` e é preciso rodar o Dijkstra (~3 ms no grafo sintético). O teste é conservador: pode dizer `False` com a rota ainda ótima, mas não deve dizer `True` com ela superada. Em 600 casos conferidos contra o Dijkstra, 52 deram `True` e todos foram confirmados; não houve nenhum `True` errado.

**4. E se uma aresta da própria rota mudou?**
Também devolve `False`: o custo da rota mudou (e, se piorou, talvez haja alternativa melhor). Se só melhorou, a rota provavelmente continua ótima, mas a função não tenta provar isso; é uma escolha de simplicidade.

**5. Por que manter o último valor em vez do fallback quando a consulta falha?**
O fallback do OSM (`maxspeed` ou padrão da via) não sabe do trânsito. Sobrescrever com ele um valor real, recente, de um trecho congestionado faria a rota voltar a passar por ali por causa de um erro de rede passageiro. O valor antigo é uma estimativa melhor que o fallback. O preço: o dado envelhece e a falha só aparece na contagem `falhas`; o ponto não avança em `ultima` e volta ao começo da fila.

**6. Existe Dijkstra dinâmico? Por que não usar?**
Existe: algoritmos como o de Ramalingam e Reps mantêm a árvore de caminhos mínimos e reparam só a parte afetada por uma mudança de peso. Não usamos porque, com o Dijkstra em ~3 ms no grafo sintético, não há custo de cálculo relevante a poupar, e eles trazem estruturas e casos extras (aumento e redução de peso). O argumento depende dessa medição; em um grafo muito maior ou com muitas rotas por segundo teria de ser reavaliado (não medido).

**7. Qual a complexidade?**
`indexar`: O(E) com o cálculo do ponto médio de cada aresta TomTom. `atualizar_transito`: ordenar os pontos O(P log P) e, por ponto escolhido, uma consulta (a parte cara) mais O(arestas do ponto) para comparar e reescrever. `rota_continua_otima`: O(A), com A as arestas alteradas, mais busca de interseção com a rota. O Dijkstra continua O((E+V) log V). Medido: ~2,7 a 3,5 ms para a atualização com consulta falsa, de 5% a 100% dos pontos.

**8. Como o orçamento distribui a cota?**
Os pontos são ordenados por `ultima` crescente (nunca consultados primeiro, 0) e os `orcamento` primeiros são consultados. Cada ciclo avança a fila: com 211 pontos e orçamento 50, cinco ciclos passam por todos, em rodízio, e o que ficou de fora aparece em `pulados_por_orcamento`. Não há prioridade por importância da via. Ponto que falha não avança em `ultima` e pode ocupar a cota de todo ciclo (limitação conhecida).

**9. Para que serve a tolerância?**
Para não reescrever (e invalidar rotas) por ruído: se `v_livre` e `v_atual` mudaram menos de `tolerancia_kmh` (padrão 1 km/h, escolhido por nós, não calibrado), a aresta fica como está. A comparação é sempre com o valor gravado, então pequenas mudanças não se acumulam sem ser notadas: quando a soma passa da tolerância, a aresta é reescrita.

**10. Por que `litros` e `t_livre` não seguem a regra de `t_atual`?**
`litros` vem de uma curva em U: se a velocidade sobe, o tempo cai, mas o consumo pode subir ou cair conforme o lado da curva. Por isso "melhorou" é medido no próprio peso, usando os valores anteriores guardados em `Resultado.anteriores`, e não pelos conjuntos `pioraram`/`melhoraram` (que são por `t_atual`). O mesmo vale para `t_livre`, que depende de `freeFlowSpeed` e pode mudar. Só `length` é imune ao trânsito.

**11. Então os dados do grafo ficam consistentes entre si?**
Cada aresta é consistente (velocidade, tempos e litros gravados juntos), mas arestas diferentes podem ter idades diferentes. Uma rota soma trechos de momentos distintos. `indice.ultima` guarda o instante de cada ponto; o planejador ainda não usa essa informação.
