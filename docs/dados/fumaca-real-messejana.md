# Teste de fumaça com dados reais: Messejana

Medido com `scripts/fumaca_real.py` em 2026-11-16 (osmnx 2.1.2, Overpass público, sem TomTom, sem cache HTTP do osmnx).
Os tempos e contagens abaixo vêm da PRIMEIRA versão do script. A versão atual acrescenta três medições (seção "Pendente de medição") que NÃO foram rodadas: o Overpass ficou inacessível na revisão.
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

Os tipos acima mostram `list` para `highway`, `name` e `maxspeed` em algumas arestas, o que indica que `ox.load_graphml` restaurou listas. A checagem direta (nenhum valor str começando com `[`) está na seção "Pendente de medição" e ainda não foi executada.

## Rota de teste

Origem -3,84244, -38,49937 (vértice 2858690121) até -3,81661, -38,48454 (vértice 2503401256), extremos sudoeste e nordeste da maior componente fortemente conectada.

| Critério | Distância | Tempo | Consumo |
|---|---|---|---|
| menor distância | 4,43 km | 7,80 min | 0,35 L |
| menor tempo | 4,89 km | 6,92 min | 0,35 L |
| menor consumo | 4,43 km | 7,80 min | 0,35 L |

Sem trânsito (`v_atual = v_livre`), consumo e distância escolhem o mesmo caminho nesta rota; o de menor tempo é 0,46 km mais longo e 0,88 min mais rápido.

## Pendente de medição

Em 2026-11-16, ao rodar a versão atual do script, `overpass-api.de` não respondeu: `ConnectTimeout` do `requests` em 3 execuções seguidas e, depois, 6 tentativas com 1 minuto de intervalo (o `curl` a `/api/status` falhou no handshake TLS, código 000; os espelhos `overpass.kumi.systems` e `overpass.private.coffee` também deram 000, `overpass.openstreetmap.fr` 403 e `maps.mail.ru` 504). Google e Nominatim responderam 200 da mesma máquina, então a internet funcionava. Por isso os itens abaixo estão implementados no script mas SEM resultado:

| Medição | O que o script imprime | Resultado |
|---|---|---|
| Grafo baixado x grafo lido | igualdade de nós e de `edges(keys=True)`; arestas com `length`, `highway`, `name` ou `maxspeed` diferentes (esperado 0), com exemplos | não medido |
| Lista virada texto | quantos valores str de `highway`/`name`/`maxspeed` começam com `[` (esperado 0) | não medido |
| Tempo por etapa do download | cronômetros em `geocode_to_gdf`, `_overpass_request`, `_create_graph`, `simplify_graph`, `largest_component`, `add_edge_lengths` | não medido |
| Rede contra Python no download | cProfile com tempo próprio agrupado (osmnx, rede/E/S, outros) e as 15 funções mais pesadas | não medido |

Para preencher: `./.venv/Scripts/python.exe scripts/fumaca_real.py` (três downloads, cerca de 75 s cada se o Overpass estiver normal) e copiar a saída para esta página.
Só a checagem da lógica de comparação foi feita, num grafo sintético de 2 vértices e 1 aresta (0 diferenças, 0 valores começando com `[`); isso valida o código do script, não o grafo de Messejana.
