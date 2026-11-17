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
Em Messejana, sim, nos campos comparados (medido em 2026-11-17). O `scripts/fumaca_real.py` compara o grafo baixado com o lido do `.graphml`: mesmo conjunto de nós (746 e 746), mesmo `edges(keys=True)` (1870 e 1870) e 0 arestas com `length`, `highway`, `name` ou `maxspeed` diferentes. Deu 0 diferenças com o download pelo Overpass e com o download pela API do OSM (fonte alternativa, [FAQ](faq-fonte-alternativa.md)); a fonte é gravada no arquivo e lida de volta. O que isso não prova: atributos fora desses quatro, outros lugares ou outras versões do osmnx. Detalhes em [dados/fumaca-real-messejana.md](../dados/fumaca-real-messejana.md).

**6. E as ruas paralelas (multigrafo)? O arquivo as preserva?**
Sim. O graphml grava a `key` de cada aresta e o osmnx devolve um `MultiDiGraph`. Ruas paralelas e mão única (dirigido) continuam distintas; entre paralelas o Dijkstra usa a de menor peso.

**7. Quais atributos podem voltar diferentes do arquivo?**
O XML só guarda texto, então o osmnx converte de volta: `length` e coordenadas viram float, `geometry` volta LineString, e `highway`, `name` e `maxspeed` voltam como str ou como lista quando a aresta tinha vários valores. Em Messejana, `highway`, `name` e `maxspeed` apareceram como `list` em algumas arestas depois da leitura; a checagem direta foi executada em 2026-11-17 e nenhum valor str de `highway`, `name` ou `maxspeed` começa com `[` (0 ocorrências, nas duas fontes). Por isso os pesos que calculamos não são gravados: não dependem dessa conversão.

**8. Por que atualizar a cada 30 dias e não a cada execução?**
É um compromisso entre frescor e custo: baixar levou de 74 a 106 s pelo Overpass (medido, seis execuções em dois dias; pela API do OSM, 46,8 a 49,6 s em 4 execuções) e depende de um serviço público que às vezes recusa pedidos, e a rede viária de um bairro muda devagar. O valor é um parâmetro (`validade_dias`) e `--atualizar-grafo` força a atualização.

**9. Um arquivo corrompido derruba o programa?**
Não. Qualquer erro ao ler faz o programa baixar de novo e regravar. A gravação usa arquivo temporário e `replace`, então uma interrupção não deixa arquivo meio escrito.
