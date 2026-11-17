# 002. Rotas alternativas (k melhores rotas)

Status: aceita (2026-11-17).

## Contexto

O planejador (etapa 5) devolve uma rota por critério (distância, tempo, consumo), a ótima segundo o Dijkstra escrito à mão em `rotas.py`. O quadro desenha um grafo pequeno com vários caminhos até o mesmo vértice (pesos 4, 5 e 6; `d[v] = 38` riscado e `39`) e o `analisar.md` pede "criar as trajetórias e escolher a de menor tempo".

**Interpretação adotada (do quadro, não confirmada com o autor):** o Dijkstra já escolhe a trajetória de menor custo; as alternativas são as próximas melhores, para quem quiser comparar. Não é um pedido de enumerar todas as trajetórias (a skill `quadro-modelagem` descarta isso por ser exponencial).

## Problema

Só a ótima não basta quando o motorista quer comparar opções (uma rua que prefere evitar, uma rota um pouco mais longa e mais simples). E "as 3 próximas melhores" calculadas do jeito mais direto não resolvem, como mostra a causa.

## Causa

1. **Por que só a ótima não basta:** o Dijkstra devolve um caminho por origem e destino. As outras opções não estão guardadas em lugar nenhum: `pred` guarda só o melhor predecessor de cada vértice.
2. **Por que o Yen puro devolve quase-duplicatas:** as k menores rotas em custo são, por construção, as que mais se parecem com a ótima. Trocar um único quarteirão por outro quase equivalente custa pouco e entra na lista antes de qualquer rota realmente diferente. Medido em grafo sintético: ver a seção "Evidência" (sobreposição da 2ª rota de Yen com a ótima).

## Decisão

Em `src/tonton/rotas.py`:

- `dijkstra` e `menor_rota` ganham os parâmetros opcionais, só por nome, `ignorar_vertices` e `ignorar_arestas` (arestas como `(u, v, chave)`). O filtro é feito dentro do laço; o grafo nunca é copiado nem alterado.
- `menores_rotas(G, origem, destino, k=3, peso="t_atual")`: algoritmo de **Yen** para os k menores caminhos **sem laços**, em custo crescente. Parte da melhor rota; para cada vértice dela (o "desvio") calcula o melhor caminho até o destino proibindo (a) os vértices anteriores da rota (a raiz, para não formar laço) e (b) os trechos que as rotas já aceitas com a mesma raiz usaram para sair do desvio. Os candidatos entram numa fila de prioridade e o de menor custo é a próxima rota. Empates de custo: ordem de descoberta (determinística).
- `rotas_alternativas(G, origem, destino, k=3, peso, max_sobreposicao=0.8, max_candidatos=50)`: pega os candidatos de Yen (no máximo `max_candidatos`, contando a ótima) e só aceita um se a fração do seu comprimento (`length`, em metros; arestas sem `length` contam 0) que coincide com as arestas de UMA rota já aceita for <= `max_sobreposicao`.
- **Identidade da rota = sequência de vértices.** Em multigrafo, a aresta usada em cada trecho é a de menor peso, como em `menor_rota`; ao proibir a saída de um desvio, todas as paralelas daquele trecho são proibidas juntas. Assim duas arestas paralelas nunca viram duas "rotas diferentes" pelos mesmos cruzamentos.
- Origem igual ao destino: `[rota vazia]`. Destino inalcançável: `RotaInexistente`. Menos de k rotas existentes: devolve as que há.

Em `planejador.py`: `planejar_alternativas(G, origem, destino, criterio, k, max_sobreposicao)` devolve `list[Resumo]` (totais de distância, tempo e litros somados nas arestas escolhidas, como em `planejar`); `geojson_colecao` grava uma Feature por rota com `indice` (0 = ótima); `comparar` aceita também uma lista (linhas "ótima", "alt 1", "alt 2"...). Na CLI: `--alternativas K` (padrão 1, comportamento anterior) e `--max-sobreposicao` (0 a 1, padrão 0,8).

## Alternativas descartadas

- **Enumerar todos os caminhos e ordenar:** o número de caminhos sem laço cresce exponencialmente com o tamanho do grafo (é o que a skill do quadro já proíbe). O Yen só gera os k de que precisa.
- **Penalizar as arestas já usadas e rodar o Dijkstra de novo (método da penalidade):** simples e rápido, mas o resultado não é "a 2ª melhor rota" (o custo muda com a penalidade) e não há garantia de ordem nem de que nenhuma rota boa ficou de fora. Ficou como possível melhoria futura para o filtro de diversidade; não foi medido.
- **Rotas de plateau / via-nodes:** produzem alternativas muito diferentes e rápidas em redes grandes (usam duas árvores de caminhos mínimos, uma da origem e outra do destino), mas são mais difíceis de explicar e de testar, e o objetivo aqui é didático. Não implementado nem medido.
- **Yen puro sem filtro:** rejeitado pela causa 2.

## Consequências e riscos

- **Custo:** cada rota aceita gera até um candidato por vértice da rota anterior, e cada candidato é um Dijkstra: no pior caso O(k · |V| · (E + V) log V). O filtro de sobreposição pode exigir muitos candidatos até achar k rotas diferentes; `max_candidatos` limita o custo e, ao estourar, devolve menos de k rotas. Números na seção "Evidência".
- **Sem laços:** nenhuma rota repete cruzamento. Uma rota que faria um retorno (contorno de quarteirão) não aparece, o que é desejado.
- **Pesos não negativos:** como no Dijkstra, peso negativo levanta `ValueError`.
- **Multigrafo:** ver a decisão acima; rotas que só diferem pela aresta paralela são a mesma rota.
- **Sobreposição por comprimento:** é uma heurística de "parecença", não prova que duas rotas são úteis de formas diferentes. O limite 0,8 é um padrão escolhido por nós, não calibrado em dados reais.
- **Ordem entre critérios:** cada critério tem a sua lista, ordenada pelo próprio peso; um Resumo "alt" pode ser melhor que a ótima em outra coluna (distância, tempo ou litros).
- **Dados reais:** nada disto foi medido em Messejana (o Overpass esteve inacessível; ver [dados/fumaca-real-messejana.md](../dados/fumaca-real-messejana.md)).

## Evidência

Benchmark em **grafo sintético** (grade n x n, mão dupla, pesos aleatórios com semente fixa), **não é Messejana**. Script: `scripts/bench_alternativas.py`; resultados completos e ambiente em [dados/bench-alternativas.md](../dados/bench-alternativas.md).

Ambiente: Python 3.11.15, networkx 3.6.1, Windows 10, semente 42, peso `t_atual`; origem e destino em cantos opostos. Uma máquina, uma sessão: os tempos valem como ordem de grandeza, não como garantia.

**Correção (oráculo).** Em 200 grafos aleatórios de 7 vértices, com arestas paralelas, 14 não tinham caminho entre origem e destino (nada a comparar); nos outros 186, as listas de custos de `menores_rotas` coincidiram com a enumeração de todos os caminhos simples em 186 de 186 casos. Isso confere o que o Yen devolve, não o custo em grafos grandes.

**Tempo de `menor_rota` contra `menores_rotas` (mediana):**

| grade | vértices | arestas | `menor_rota` | Yen k=3 | Yen k=5 | Yen k=10 |
|---|---|---|---|---|---|---|
| 30x30 | 900 | 3480 | 12,6 ms | 1,40 s | 1,73 s | 3,41 s |
| 60x60 | 3600 | 14160 | 37,5 ms | 8,28 s | 15,1 s | 33,1 s |

Para k=3, o Yen custou cerca de 110 vezes a `menor_rota` na grade 30x30 e cerca de 220 vezes na 60x60 (razões das medianas acima). Hipótese (não medida por etapa): a 2ª rota de Yen exige um Dijkstra por vértice da ótima, e na grade maior a ótima tem mais vértices e cada Dijkstra percorre mais nós. O Yen como está (Dijkstra completo por candidato, sem reaproveitar árvores) não serve para grafos muito maiores que Messejana; Messejana tem 746 vértices, menos que a grade 30x30, mas o tempo nela **não foi medido**.

**Quase-duplicatas (Yen puro, sem filtro).** A sobreposição por comprimento da 2ª e da 3ª rotas de Yen com a ótima:

| grade | 2ª x ótima | 3ª x ótima | custo da 2ª em relação à ótima |
|---|---|---|---|
| 30x30 | 96,4% | 90,6% | +0,1% (383,8 s contra 383,4 s) |
| 60x60 | 88,0% | 98,2% | +0,07% (762,6 s contra 762,1 s) |

Ou seja, as rotas seguintes são a mesma rota com um pequeno desvio, como previsto na causa 2.

**Candidatos até achar k alternativas distintas (limite de 100 candidatos):**

| grade | k | `max_sobreposicao` | candidatos gerados | rotas aceitas | tempo |
|---|---|---|---|---|---|
| 30x30 | 3 | 0,8 | 11 | 3 | 4,8 s |
| 30x30 | 5 | 0,8 | 44 | 5 | 17,2 s |
| 30x30 | 3 | 0,5 | 100 | 1 (não achou) | 44,5 s |
| 60x60 | 3 | 0,8 | 64 | 3 | 242 s |
| 60x60 | 5 | 0,8 | 100 | 3 (não achou) | 392 s |
| 60x60 | 3 | 0,5 | 100 | 1 (não achou) | 395 s |

Leitura, limitada a estes grafos: com `max_sobreposicao` 0,8 foram precisos 11 a 64 candidatos para 3 rotas; com 0,5 nenhuma alternativa apareceu entre 100 candidatos. O padrão `max_candidatos=50` do código **não** acharia 3 rotas na grade 60x60 (precisou de 64), e os 100 candidatos já levam minutos nela. Essa grade, com pesos aleatórios independentes e centenas de caminhos quase empatados, é um caso difícil para o filtro; não prova nada sobre ruas reais, onde a diferença entre caminhos costuma ser maior (não medido). Por isso o limite padrão e a sobreposição de 0,8 ficam como valores iniciais a calibrar com dados reais.

**Pontos não resolvidos:** (1) medir em Messejana quando o Overpass voltar; (2) se o custo for problema, reaproveitar as árvores de caminhos mínimos ou usar o filtro de diversidade durante a geração (não medido).
