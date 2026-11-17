# FAQ: fonte alternativa do grafo (API do OSM)

Perguntas que um professor de grafos faria. Contexto completo em [decisoes/004-fonte-alternativa-api-osm.md](../decisoes/004-fonte-alternativa-api-osm.md); números em [dados/comparacao-fontes-messejana.md](../dados/comparacao-fontes-messejana.md).

**1. Por que o Overpass e a API devolvem dados diferentes "em forma"?**
Os dois leem o mesmo banco do OSM, mas respondem perguntas diferentes. O Overpass executa uma consulta: "ways com `highway` que NÃO sejam footway, cycleway... dentro deste polígono", e devolve só isso. A API `/map?bbox=` não filtra nada: devolve tudo (nós, ways de qualquer tipo, relações) que toca um retângulo. Em Messejana (medido em 2026-11-17, bbox com buffer de 500 m) a API devolveu 270.687 nós e 51.903 ways: só 2.796 têm `highway` e 30.544 são prédios; depois do filtro `drive` ficaram 1.380 ways. Se o osmnx lesse isso direto, o grafo teria calçadas e escadas como se fossem ruas. Por isso o projeto aplica o filtro depois de baixar.

**2. O que é um polígono de recorte e por que o osmnx usa dois?**
É o contorno do lugar (aqui, o limite de Messejana vindo do Nominatim). Uma rua que cruza a fronteira vem inteira no download, com nós fora do contorno. O osmnx primeiro baixa um polígono 500 m maior (para que cruzamentos perto da borda tenham todos os vizinhos), monta e simplifica o grafo, e só depois remove os vértices fora do contorno original. Assim os vértices da borda ainda sabem quantas ruas chegam neles (`street_count`). O download pela API segue a mesma ordem.

**3. O que é `network_type`?**
É um nome para um conjunto de regras de filtro sobre as tags do OSM. `"drive"` quer dizer "vias onde carro pode circular": exige a tag `highway`, descarta tipos como footway, cycleway, path, steps, service, e vias marcadas `motor_vehicle=no`, `motorcar=no`, `access=private` ou `area=yes`, e serviços como alley, driveway e parking_aisle. Outros tipos (`walk`, `bike`, `all`) dão grafos diferentes do mesmo lugar. O tipo muda o grafo: a mesma rua pode ser aresta em `walk` e não existir em `drive`.

**4. Por que o filtro precisa ser reproduzido na fonte alternativa?**
Porque no Overpass o filtro roda no servidor e na API não existe. O `ox.graph_from_xml` lê um arquivo OSM e monta o grafo com tudo o que está nele, sem aplicar `network_type`. Sem reaplicar o filtro, o resultado seria outro grafo (outros vértices, outras arestas, outras rotas). O filtro é lido do próprio osmnx instalado, para acompanhar a versão. Detalhe que vale conferir em aula: na Overpass a expressão `!~"no"` é uma busca por trecho (não ancorada) e uma tag ausente passa no filtro; o código em Python reproduz isso com `re.search`.

**5. Quais são os limites da API?**
Dois, e o segundo foi surpresa: o bbox não pode passar de 0,25 grau², e um pedido não pode ter mais de 50.000 nós. O bbox de Messejana é bem menor que 0,25 grau², mas a API recusou (400) porque a região tem muito mais de 50.000 nós (prédios, calçadas...). O código divide o retângulo em quartos quando a API recusa, até 3 níveis, e une as respostas pelo identificador. Em Messejana foram 21 pedidos, 16 aceitos. Cidades inteiras não cabem; nesse caso o código dá erro claro (área) ou desiste depois de 3 divisões.

**6. Se unimos vários retângulos, não duplicamos ruas e cruzamentos?**
Uma rua que cruza o limite entre dois retângulos aparece nos dois pedidos, com os mesmos identificadores (`id` do way e dos nós). Ao unir, os elementos ficam em dicionários indexados pelo `id`, então cada um entra uma vez. Sem essa chave estável, a união criaria vértices duplicados e o grafo ficaria desconexo.

**7. O grafo da API é o mesmo que o do Overpass?**
Em Messejana, baixados no mesmo momento, sim nos atributos que comparamos: mesmos vértices, mesmas arestas (com `key`) e nenhuma diferença nos atributos (ver o arquivo de dados para a lista exata). Isso vale para esse lugar, esse dia e esta versão do osmnx; não provamos para outros lugares nem para dados de dias diferentes (o OSM é editado o tempo todo). Por isso o grafo guarda `G.graph["fonte"]`: se um resultado parecer estranho, dá para saber de onde vieram os dados.

**8. Por que não escondemos qualquer erro e usamos o fallback sempre?**
Porque um fallback largo mascara bugs. Só caem para a API as falhas de rede ou de servidor (`requests.exceptions.RequestException` e o erro de status do osmnx). Um erro de programação, ou um lugar que não existe, continua explodindo na hora, em vez de produzir um grafo vindo de outro lugar sem ninguém notar. O aviso no log diz que a fonte alternativa foi usada.
