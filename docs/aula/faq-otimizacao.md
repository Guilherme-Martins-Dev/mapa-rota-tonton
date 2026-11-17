# FAQ: otimização do Yen (Lawler + A*)

Perguntas que um professor de grafos faria sobre a otimização das rotas alternativas. Contexto completo em [decisoes/005-otimizacao-yen-astar.md](../decisoes/005-otimizacao-yen-astar.md); números em [dados/bench-otimizacao.md](../dados/bench-otimizacao.md) (grafo real de Messejana, trânsito simulado).

**1. O A* devolve sempre o caminho ótimo?**
Sim, se a heurística h for admissível (nunca maior que o custo real até o destino) e, na versão que fecha cada vértice uma única vez (a nossa), também consistente. Com h = 0 o A* é o Dijkstra. O que muda é a ordem em que os vértices saem da fila: em vez de "o mais perto da origem", sai "o de menor dist + h", isto é, o mais promissor para chegar ao destino. Conferimos na prática: 0 divergências de custo (tolerância 1e-9) em 450 comparações (peso x k x par) + 150 pela API pública no grafo real de Messejana, e em 2760 comparações em 200 grafos aleatórios pequenos, inclusive com `length` menor que a distância das coordenadas (números em [dados/bench-otimizacao.md](../dados/bench-otimizacao.md)).

**2. Qual a diferença entre heurística admissível e consistente?**
Admissível: h(v) <= custo do melhor caminho de v ao destino, para todo v. Consistente (ou monótona): h(u) <= w(u, v) + h(v) para toda aresta (u, v), e h(destino) = 0. Consistente implica admissível (some as desigualdades ao longo do melhor caminho); o contrário não vale. Consistência equivale a dizer que a estimativa f = dist + h nunca diminui ao longo de um caminho.

**3. Por que o código fecha o vértice na primeira vez que ele sai da fila (`pronto`) e isso exige consistência?**
Com h consistente, f é não decrescente ao longo de qualquer caminho, então o primeiro caminho que tira u da fila já é o de menor dist até u, como no Dijkstra. Com h só admissível, um vértice pode sair da fila por um caminho caro e depois ser alcançado por outro mais barato; o A* correto teria de reabri-lo, e o nosso `pronto` o ignoraria, devolvendo uma rota não ótima. Por isso a heurística construída aqui é consistente por construção (pergunta 5).

**4. O que acontece se a heurística superestimar?**
O A* pode fechar o destino por um caminho que não é o menor: ele "acredita" que um desvio é caro demais e nunca o explora. O resultado ainda é um caminho válido, mas deixa de ser garantidamente ótimo, e o Yen em cima dele deixaria de ordenar corretamente as k rotas. É por isso que a heurística leva uma escala de segurança (pergunta 6) e o benchmark confere os custos contra o Yen original, inclusive em grafos aleatórios onde `length` é menor que a distância das coordenadas (a situação em que uma heurística ingênua superestimaria).

**5. Por que a distância haversine é um limite inferior da distância viária?**
A haversine é o comprimento do menor caminho sobre a esfera entre dois pontos; qualquer rua é um caminho sobre a esfera (aproximadamente), logo mais longo ou igual. Para a aresta (u, v), `length` (medido ao longo da geometria da rua) é >= haversine(u, v) no OSM real. Como a haversine obedece à desigualdade triangular, haversine(u, destino) <= haversine(u, v) + haversine(v, destino); multiplicando por uma constante c com c × haversine(u, v) <= w(u, v) para toda aresta, obtém-se h(u) <= w(u, v) + h(v): a consistência. Ressalva: a Terra é tratada como esfera (o osmnx também usa esfera para calcular `length`), não como elipsoide.

**6. Como a constante c é escolhida para cada peso?**
c = r_min × escala, onde r_min é o menor valor de peso/length entre as arestas e escala = min(1, menor length/haversine(u, v)). Para `length`, r_min = 1 (peso e comprimento são a mesma coisa): h é a distância em linha reta em metros. Para `t_atual`, r_min = 1/v_max em s/m: a estimativa é "a reta, na velocidade mais alta da rede". Para `litros`, r_min é o menor litros por metro. A escala só entra quando alguma aresta tem `length` menor que a distância das coordenadas, o que não ocorre no OSM real mas pode ocorrer em grafos de teste; sem ela a heurística poderia superestimar.

**7. Qual a complexidade do Yen e o que a modificação de Lawler muda?**
Cada rota aceita gera um candidato por vértice da rota anterior, e cada candidato é um Dijkstra: com n vértices e m arestas, o pior caso para k rotas é O(k · n · (m + n) log n). Lawler observa que, para uma rota-filha que se desviou da rota-pai no índice j, os desvios nos índices menores que j têm a mesma raiz e as mesmas arestas proibidas da rota-pai, e já foram calculados quando a rota-pai foi expandida; só os desvios a partir de j são novos. A complexidade assintótica do pior caso não muda; muda a constante (menos Dijkstras por rota aceita). O ganho medido está no registro 005.

**8. Por que não usar A* desde o início, sem medir antes?**
Porque otimização sem causa medida é suposição. A regra do projeto é medir primeiro (aqui: tempo por consulta, número de Dijkstras, vértices expandidos e um profile), depois implementar cada candidata isoladamente e aceitá-la só se reduzir o tempo medido e mantiver os custos idênticos. Um dos achados do profile foi um custo que ninguém tinha suposto: uma pré-checagem (`G.number_of_edges()` + varredura de arestas) repetida a cada Dijkstra, respondendo por cerca de 33% do tempo de uma consulta típica (`builtins.sum` + `reportviews` + `coreviews` + `_collections_abc` no cProfile); ver o registro 005. Nem toda candidata mediu bem: a poda de spurs (C) não cortou nenhum desvio nos testes em Messejana (mesmo número de Dijkstras com e sem ela) e às vezes piorou o tempo; ficou implementada mas desligada por padrão.

**9. O A* funciona com os três pesos (distância, tempo, consumo)?**
Funciona com qualquer peso não negativo para o qual se consiga um c tal que peso >= c × haversine(u, v) em toda aresta: o código calcula c varrendo as arestas, então vale para `length`, `t_atual`, `t_livre` e `litros`. O quanto ele ajuda depende do peso: quanto mais o peso é proporcional à distância, mais apertada é a estimativa e menos vértices são expandidos. Os ganhos por peso estão em [dados/bench-otimizacao.md](../dados/bench-otimizacao.md).

**10. E se os pesos mudam com o trânsito?**
Se a heurística ficasse guardada no grafo, `atualizar_transito` poderia aumentar uma velocidade e tornar o r_min guardado grande demais, e a heurística passaria a superestimar. Por isso c é recalculado a cada consulta, varrendo as arestas com os pesos de agora (custo O(m) por consulta, e uma vez por chamada de `menores_rotas`, não por Dijkstra). Se o grafo muda no meio de uma consulta, nada garante nada; o planejador não faz isso.
