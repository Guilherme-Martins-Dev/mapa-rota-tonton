# FAQ: rotas alternativas

Perguntas que um professor de grafos faria sobre as rotas alternativas. Contexto completo em [decisoes/002-rotas-alternativas.md](../decisoes/002-rotas-alternativas.md); números em [dados/bench-alternativas.md](../dados/bench-alternativas.md) (grafo sintético, não Messejana).

**1. Por que Yen e não "rodar o Dijkstra várias vezes"?**
Rodar o Dijkstra de novo sobre o mesmo grafo devolve a mesma rota ótima. Para obter a próxima é preciso proibir algo. O Yen faz isso de forma sistemática: parte da melhor rota e, em cada vértice dela (o "desvio"), proíbe o trecho que as rotas já aceitas usaram a partir dali e proíbe voltar aos vértices do começo da rota (a "raiz"). Cada candidato é o melhor caminho possível sob essas proibições, então nenhum caminho fica de fora.

**2. O que garante que a 2ª rota é a 2ª melhor?**
Todo caminho sem laços diferente da ótima se separa dela num primeiro vértice. Para esse vértice de desvio, o Yen calcula o melhor caminho com a mesma raiz e outro próximo trecho; logo o 2º melhor caminho está entre os candidatos gerados. A fila de candidatos é ordenada por custo e o de menor custo é aceito. Isso vale com pesos não negativos, em que o Dijkstra é exato. Conferimos também na prática: o Yen coincidiu com a enumeração de todos os caminhos em grafos pequenos (ver o oráculo em [dados/bench-alternativas.md](../dados/bench-alternativas.md)).

**3. Por que "sem laços"?**
Sem essa restrição, a 2ª melhor "rota" costuma ser a ótima com um passeio extra num quarteirão (ir e voltar), e há infinitos caminhos com laço. Exigir que nenhum vértice se repita (caminho simples) torna o conjunto finito e a ordem bem definida. É também o que um motorista entende por rota alternativa. O Yen garante isso por proibir os vértices da raiz na busca do trecho de desvio.

**4. O que acontece com ruas paralelas (multigrafo)?**
Duas arestas paralelas u->v entre os mesmos cruzamentos não geram duas rotas: a identidade de uma rota é a sequência de vértices, e em cada trecho vale a aresta de menor peso, como em `menor_rota`. Ao proibir a saída de um desvio, todas as paralelas daquele trecho são proibidas juntas, senão a aresta paralela pior apareceria como "outra rota" com os mesmos cruzamentos.

**5. Qual a complexidade?**
Cada rota aceita gera até |V| candidatos (um por vértice da rota anterior), e cada candidato custa um Dijkstra, O((E+V) log V) com heap. Para k rotas: O(k·|V|·(E+V) log V) no pior caso. Na prática o caminho tem bem menos vértices que |V|. Os tempos medidos em grades sintéticas estão em [dados/bench-alternativas.md](../dados/bench-alternativas.md); não medimos em Messejana.

**6. Por que filtrar por sobreposição?**
O Yen puro devolve as rotas em ordem de custo, e as primeiras costumam diferir da ótima por um quarteirão: o mesmo caminho com um pequeno desvio. Num mapa isso não ajuda quem decide. O filtro aceita um candidato só se, no máximo, `max_sobreposicao` (padrão 0,8) do seu comprimento coincidir com as arestas de uma rota já aceita. O preço é gerar mais candidatos (limitado por `max_candidatos`); se o grafo não tiver rotas suficientemente diferentes, devolve menos de k.

**7. O Dijkstra funciona com pesos negativos? E o Yen?**
Não. O Dijkstra fixa a distância de um vértice ao retirá-lo da fila, o que só é correto se nenhum caminho posterior puder diminuí-la, ou seja, com pesos não negativos. O código levanta `ValueError` ao achar peso negativo. O Yen herda a restrição, pois chama o Dijkstra. Tempo, distância e litros são sempre não negativos.

**8. O grafo é alterado ao proibir vértices e arestas?**
Não. `dijkstra` e `menor_rota` recebem `ignorar_vertices` e `ignorar_arestas` e pulam esses itens dentro do laço. Remover e recolocar arestas (ou copiar o grafo) a cada candidato custaria tempo e deixaria o grafo errado se houvesse uma exceção no meio.

**9. E se origem for igual ao destino, ou o destino for inalcançável?**
Origem igual ao destino devolve uma única rota vazia (custo 0). Destino inalcançável levanta `RotaInexistente`, como em `menor_rota`. Se existirem menos de k rotas, devolve as que existem.

**10. A alternativa mais lenta pode ser a de menos consumo?**
Pode. Cada critério (distância, tempo, consumo) tem as suas k rotas, ordenadas pelo próprio peso; os totais dos três são sempre somados sobre as arestas escolhidas, então a tabela mostra o que se ganha e se perde em cada coluna. A ordenação dentro de um critério é só pelo peso daquele critério.
