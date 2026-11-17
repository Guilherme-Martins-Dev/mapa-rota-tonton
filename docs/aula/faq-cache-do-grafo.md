# FAQ: cache do grafo viário

Perguntas que um professor de grafos faria sobre o cache. Contexto completo em [decisoes/001-cache-do-grafo.md](../decisoes/001-cache-do-grafo.md).

**1. Por que não cachear também os pesos?**
Porque a estrutura do grafo (vértices e arestas) muda em meses, enquanto os pesos mudam em minutos (trânsito) ou com o veículo escolhido. Separar estrutura de pesos permite recalcular `t_atual` e `litros` sempre, sem baixar nada. Além disso, pesos são derivados: guardá-los criaria dados que podem divergir da fórmula atual.

**2. O que muda se uma rua ganhar mão única?**
Muda a estrutura: uma das arestas (u,v) ou (v,u) deixa de existir. Com cache antigo, o programa ainda usaria o sentido proibido. É o risco do cache; por isso há a validade de 30 dias e o `--atualizar-grafo`. Depois do download novo, o grafo e as rotas refletem a mudança.

**3. Por que graphml e não pickle?**
`graphml` é XML padronizado, legível e sem execução de código ao ler. `pickle` executa código ao carregar um arquivo não confiável e é frágil entre versões do Python e do NetworkX. Não comparamos velocidades. O graphml exige conversão de tipos ao ler (pergunta 7); a leitura de Messejana levou 0,12 s.

**4. Como o cache afeta a corretude do Dijkstra?**
Não afeta o algoritmo: o Dijkstra exige pesos não negativos e devolve o caminho ótimo para o grafo que recebe. O cache só decide qual grafo ele recebe. Se o arquivo for fiel ao OSM do momento do download, o resultado é ótimo para aquele grafo; se estiver velho, é ótimo para um mapa velho.

**5. Ler do arquivo gera o mesmo grafo que baixar?**
Ainda não medido. O script `scripts/fumaca_real.py` compara o grafo baixado com o lido (mesmos nós, mesmo `edges(keys=True)`, e `length`, `highway`, `name`, `maxspeed` iguais aresta a aresta), mas o Overpass ficou inacessível quando tentamos rodar. O que já foi medido: o grafo lido tem 746 vértices e 1870 arestas em Messejana, `length` float e `geometry` LineString. Resultado da comparação: ver [dados/fumaca-real-messejana.md](../dados/fumaca-real-messejana.md), seção "Pendente de medição".

**6. E as ruas paralelas (multigrafo)? O arquivo as preserva?**
Sim. O graphml grava a `key` de cada aresta e o osmnx devolve um `MultiDiGraph`. Ruas paralelas e mão única (dirigido) continuam distintas; entre paralelas o Dijkstra usa a de menor peso.

**7. Quais atributos podem voltar diferentes do arquivo?**
O XML só guarda texto, então o osmnx converte de volta: `length` e coordenadas viram float, `geometry` volta LineString, e `highway`, `name` e `maxspeed` voltam como str ou como lista quando a aresta tinha vários valores. Em Messejana, `highway`, `name` e `maxspeed` apareceram como `list` em algumas arestas depois da leitura; a checagem direta de que nenhum valor str começa com `[` ainda não foi executada. Por isso os pesos que calculamos não são gravados: não dependem dessa conversão.

**8. Por que atualizar a cada 30 dias e não a cada execução?**
É um compromisso entre frescor e custo: baixar levou cerca de 74 s (medido, duas execuções) e depende de um serviço público que às vezes recusa pedidos, e a rede viária de um bairro muda devagar. O valor é um parâmetro (`validade_dias`) e `--atualizar-grafo` força a atualização.

**9. Um arquivo corrompido derruba o programa?**
Não. Qualquer erro ao ler faz o programa baixar de novo e regravar. A gravação usa arquivo temporário e `replace`, então uma interrupção não deixa arquivo meio escrito.
