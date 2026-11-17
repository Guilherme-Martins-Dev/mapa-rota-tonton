# Comparação das fontes do grafo: Overpass x API do OSM (Messejana)

Medido em 2026-11-17 (osmnx 2.1.2, sem TomTom, sem cache HTTP do osmnx). Decisão: [004](../decisoes/004-fonte-alternativa-api-osm.md). Máquina de desenvolvimento comum; tempos de rede variam.

## Referência do Overpass (2026-11-16) contra a API (2026-11-17)

Os números do Overpass são os de [fumaca-real-messejana.md](fumaca-real-messejana.md). Os da API vêm de `scripts/fumaca_real.py --fonte api` (grafo lido do `.graphml`).

| Item | Overpass (2026-11-16) | API do OSM (2026-11-17) |
|---|---|---|
| Vértices | 746 | 746 |
| Arestas | 1870 | 1870 |
| highway | residential 1568, tertiary 85, primary 64, unclassified 48, secondary 40, trunk 39, living_street 14, trunk_link 7, primary_link 7 | os mesmos nove valores, as mesmas contagens |
| Sem `name` | 8,0% | 8,0% |
| Sem `maxspeed` | 92,7% | 92,7% |
| Com `geometry` | 29,9% | 29,9% |
| Arestas para a TomTom / pontos médios distintos | 228 / 211 | 228 / 211 |
| Soma de `length` | não medido naquele dia | 159,662 km |
| Mediana de `length` | não medido naquele dia | 76,95 m |
| Componentes fortemente conexas | não medido naquele dia | 10 (maior com 737 vértices) |
| Rota sudoeste-nordeste (distância / tempo / consumo) | 4,43 km, 4,89 km, 4,43 km | idêntica nos três critérios (4,43 km / 7,80 min; 4,89 km / 6,92 min; 4,43 km / 7,80 min) |

Soma, mediana e componentes de 2026-11-16 não foram registrados, então a comparação dessas três linhas só é possível com o download de hoje (próxima seção).

## Comparação direta, no mesmo momento

Como o Overpass respondeu durante a sessão de 2026-11-17, os dois grafos foram baixados um depois do outro (Overpass 84,8 s, API 49,6 s) e comparados em memória. O código desta comparação (uma versão de rascunho, que olhava `length`, `highway`, `name`, `maxspeed`, `oneway`, `osmid`, `lanes` e `geometry` nas arestas e `x`, `y`, `street_count`, `highway` nos nós) rodou na íntegra; resultado:

| Medida | Overpass | API do OSM |
|---|---|---|
| Vértices / arestas | 746 / 1870 | 746 / 1870 |
| Soma de `length` | 159,662 km | 159,662 km |
| Mediana de `length` | 76,95 m | 76,95 m |
| Componentes fortemente conexas | 10 (maior 737) | 10 (maior 737) |
| Nós só em uma das fontes | 0 | 0 |
| `edges(keys=True)` só em uma das fontes | 0 | 0 |
| Arestas em comum com diferença nos 8 campos conferidos | 0 de 1870 | |
| Nós em comum com diferença nos 4 campos conferidos | 0 de 746 | |

O script versionado `scripts/comparar_fontes.py` faz a mesma comparação, mas sobre TODOS os atributos das arestas e dos nós. Essa versão final NÃO foi executada com sucesso: na tentativa o Overpass voltou a falhar (`ConnectTimeout`, `connect timeout=180`). O resultado acima é, portanto, o do rascunho com campos escolhidos, não o do script versionado.

## É o mesmo grafo?

O que está medido: para Messejana, com os dois downloads feitos no mesmo dia e na mesma sessão, os conjuntos de vértices e de arestas (com `key`) são iguais e não houve diferença nos campos comparados (comprimento a 1e-6 m, geometria igual, `highway`, `name`, `maxspeed`, `oneway`, `osmid`, `lanes`, coordenadas e `street_count`). Soma e mediana dos comprimentos e o número de componentes fortes também coincidem. Para o uso do projeto (pesos, Dijkstra, rotas) é, nos campos medidos, o mesmo grafo.

O que NÃO está medido: (i) atributos fora dos campos listados no rascunho; (ii) outros lugares (um bairro com mais marcações complicadas, `access`, `motor_vehicle` etc., poderia expor diferença entre o filtro do Overpass e o nosso em Python); (iii) outros dias (o OSM muda; hoje as duas fontes e a referência de ontem coincidiram, mas isso não foi garantido por construção); (iv) o grafo do Overpass de 2026-11-16 em si, que não foi guardado: dele só temos os agregados da tabela anterior. Por isso a afirmação honesta é "mesmos dados nos campos medidos, neste lugar e neste dia", não "equivalente em geral".

## Tempo do download pela API (fonte API; NÃO comparável com os 74,5 s do Overpass)

Os 74,5 s de [001](../decisoes/001-cache-do-grafo.md) eram do Overpass, em 2026-11-16. Aqui é outra fonte, em outro dia.

`scripts/fumaca_real.py --fonte api`, segundo download da execução (`baixar_via_api_osm`, total 47,23 s; o primeiro, via `carregar_grafo` + gravação, levou 46,77 s):

| Etapa | Tempo | % do total |
|---|---|---|
| Geocodificar (Nominatim) | 1,09 s | 2,3% |
| GET do XML (21 pedidos: 5 recusados com 400, 16 aceitos) | 39,90 s | 84,5% |
| Filtro `drive` + descarte de nós órfãos (inclui ler o XML em Python) | 5,54 s | 11,7% |
| `graph_from_xml` | 0,24 s | 0,5% |
| Recorte pelo buffer + maior componente | 0,21 s | 0,4% |
| Simplificação | 0,19 s | 0,4% |
| Recorte pelo polígono + maior componente + `street_count` | 0,07 s | 0,1% |

Outras execuções da API: 49,6 s (na comparação) e uma de teste, de uma chamada direta à função, cujas etapas somaram cerca de 49,4 s (GET 42,75 s, filtro 5,71 s). O GET domina; não separamos rede de servidor. Quanto ao conteúdo (bbox com buffer de 500 m, 2026-11-17): 270.687 nós e 51.903 ways únicos, dos quais 2.796 com `highway`, 30.544 prédios e 1.380 mantidos pelo filtro `drive`; as 16 respostas aceitas somaram 85,2 MB de XML (com sobreposição entre os quartos).

## Tempo do download pelo Overpass, hoje (fonte Overpass)

Quatro downloads cronometrados em 2026-11-17: 85,7 s, 84,8 s, 95,2 s e 106,0 s (74,5 s e 74,0 s em 2026-11-16). Variam de 74 a 106 s entre execuções; não há dado para afirmar tendência.
