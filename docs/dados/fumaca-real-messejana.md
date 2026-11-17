# Teste de fumaça com dados reais: Messejana

Medido com `scripts/fumaca_real.py` em 2026-11-16 (osmnx 2.1.2, Overpass público, sem TomTom, sem cache HTTP do osmnx).
Os tempos e contagens das seções "Tempos medidos" a "Rota de teste" vêm da PRIMEIRA versão do script (fonte: Overpass). As medições que ficaram pendentes foram feitas em 2026-11-17 e estão na seção "Medições que estavam pendentes", com a fonte indicada em cada uma.
Máquina de desenvolvimento comum; os tempos de rede variam de execução para execução.

## Tempos medidos

| Etapa | Tempo |
|---|---|
| (a) download do OSM sem cache (+ gravar o .graphml) | 74,51 s (outra execução: 73,96 s) |
| (b) leitura do .graphml (cache) | 0,12 s (outra execução: 0,13 s) |
| (c) `preparar_grafo` sem trânsito | < 0,01 s |
| (d) 3 rotas (distância, tempo, consumo) | 0,01 s |

Ganho do cache: cerca de 600 vezes na carga do grafo (74,5 s contra 0,12 s). O arquivo tem 0,80 MB.
Numa tentativa intermediária o Overpass respondeu `502 Bad Gateway` (servidor lotado): o download depende de um serviço público.

## O grafo

| Item | Valor |
|---|---|
| Vértices (cruzamentos) | 746 |
| Arestas (trechos) | 1870 |
| Arestas que iriam para a TomTom (`eh_tomtom`) | 228 |
| Pontos médios distintos (consultas reais) | 211 |
| Arestas sem `name` | 8,0% |
| Arestas sem `maxspeed` | 92,7% |
| Arestas com `geometry` | 29,9% |

`highway` (uma aresta com lista conta em cada tipo): residential 1568, tertiary 85, primary 64, unclassified 48, secondary 40, trunk 39, living_street 14, trunk_link 7, primary_link 7.
Os `*_link` não entram na TomTom (só trunk, primary, secondary, tertiary).

## Tipos depois do ida-e-volta pelo .graphml

| Atributo | Tipos encontrados |
|---|---|
| `length` | float em 1870 de 1870 |
| `geometry` | LineString sempre que presente |
| `highway` | str 1868, list 2 |
| `name` | str 1691, list 30, ausente 149 |
| `maxspeed` | ausente 1734, str 134, list 2 |

Os tipos acima mostram `list` para `highway`, `name` e `maxspeed` em algumas arestas, o que indica que `ox.load_graphml` restaurou listas. A checagem direta (nenhum valor str começando com `[`) foi executada em 2026-11-17: 0 ocorrências (seção "Medições que estavam pendentes").

## Rota de teste

Origem -3,84244, -38,49937 (vértice 2858690121) até -3,81661, -38,48454 (vértice 2503401256), extremos sudoeste e nordeste da maior componente fortemente conectada.

| Critério | Distância | Tempo | Consumo |
|---|---|---|---|
| menor distância | 4,43 km | 7,80 min | 0,35 L |
| menor tempo | 4,89 km | 6,92 min | 0,35 L |
| menor consumo | 4,43 km | 7,80 min | 0,35 L |

Sem trânsito (`v_atual = v_livre`), consumo e distância escolhem o mesmo caminho nesta rota; o de menor tempo é 0,46 km mais longo e 0,88 min mais rápido.

## Medições que estavam pendentes (2026-11-17)

Em 2026-11-16 o Overpass não respondeu (`ConnectTimeout` em 3 execuções e em 6 tentativas com 1 minuto de intervalo; `curl` ao `/api/status` com handshake TLS falho, status 000; os espelhos `overpass.kumi.systems` e `overpass.private.coffee` 000, `overpass.openstreetmap.fr` 403, `maps.mail.ru` 504; Google e Nominatim 200). Por isso as quatro medições abaixo ficaram sem resultado. Em 2026-11-17 foram feitas com a fonte alternativa ([decisão 004](../decisoes/004-fonte-alternativa-api-osm.md)) e, nos itens em que o Overpass voltou a responder (intermitente), com ele também. A fonte de cada número vem indicada.

| Medição | Resultado | Fonte |
|---|---|---|
| (i) Grafo baixado x grafo lido do `.graphml` | mesmo conjunto de nós (746 e 746), mesmo `edges(keys=True)` (1870 e 1870), 0 arestas com `length`/`highway`/`name`/`maxspeed` diferentes (esperado 0) | API do OSM (`--fonte api`) e também Overpass (`fonte 'overpass'`, execução automática): 0 diferenças nas duas |
| (ii) Lista virada texto | 0 valores str de `highway`/`name`/`maxspeed` começando com `[` (esperado 0) | API do OSM e Overpass: 0 nas duas |
| (iii) Tempo por etapa do download | ver tabelas abaixo | API: tabela "fonte API"; Overpass: tabela "fonte Overpass" |
| (iv) Rede contra Python no download (cProfile) | NÃO MEDIDO: o Overpass falhou com `ConnectTimeout` (`connect timeout=180`) nas duas tentativas (dentro de `fumaca_real.py` e numa chamada isolada de `baixar_com_perfil`) | Overpass |

Também com a API do OSM, o que o script já media: `preparar_grafo` sem trânsito 0,00 s; 3 rotas 0,01 s; leitura do `.graphml` 0,13 s (0,11 s com o arquivo do Overpass); arquivo de 0,80 MB; tipos após o ida-e-volta (`length` float 1870/1870; `highway` str 1868 e list 2; `name` str 1691, list 30, ausente 149; `maxspeed` ausente 1734, str 134, list 2; `geometry` sempre LineString) e rota de teste (4,43 km / 7,80 min / 0,35 L; 4,89 km / 6,92 min / 0,35 L; 4,43 km / 7,80 min / 0,35 L) iguais aos de 2026-11-16. O `.graphml` guarda a fonte (`G.graph["fonte"]`, lido de volta como `'api-osm'` ou `'overpass'`).

### Tempo por etapa, fonte Overpass (2026-11-17; os 74,5 s de 2026-11-16 eram desta fonte)

Download total cronometrado nesta execução: 106,02 s (outro, `carregar_grafo`: 95,24 s). Tempos aninhados: `_create_graph` inclui o pedido ao Overpass, porque o osmnx consome o resultado do pedido dentro dele; não somar linhas.

| Função do osmnx | Tempo | % do total |
|---|---|---|
| `geocode_to_gdf` (Nominatim) | 1,16 s | 1,1% |
| `_get_overpass_pause` (status do Overpass) | 0,68 s | 0,6% |
| `_overpass_request` (rede + servidor) | 104,07 s | 98,2% |
| `_create_graph` (inclui o pedido) | 104,21 s | 98,3% |
| `simplify_graph` | 0,19 s | 0,2% |
| `largest_component` | 0,18 s | 0,2% |
| `add_edge_lengths` | 0,02 s | 0,0% |

Leitura: com essa decomposição, cerca de 98% do tempo está no pedido ao Overpass; o resto, tudo em Python, soma cerca de 2%. Uma execução apenas, num dia em que o Overpass estava mais lento que em 2026-11-16 (74 s); separar rede de processamento no servidor não é possível com esses cronômetros.

### Tempo por etapa, fonte API do OSM (2026-11-17; NÃO comparável com os 74,5 s do Overpass)

Total 47,23 s (21 pedidos GET: 5 recusados, 16 aceitos): GET do XML 39,90 s (84,5%), filtro `drive` e nós órfãos 5,54 s (11,7%), geocodificar 1,09 s, `graph_from_xml` 0,24 s, recorte pelo buffer 0,21 s, simplificação 0,19 s, recorte pelo polígono 0,07 s. Detalhes e a comparação entre as duas fontes em [comparacao-fontes-messejana.md](comparacao-fontes-messejana.md).

Para repetir: `./.venv/Scripts/python.exe scripts/fumaca_real.py` (usa o Overpass e cai para a API se ele falhar) ou `--fonte api` para pular o Overpass.
