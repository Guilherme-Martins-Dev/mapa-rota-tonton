# 004. Fonte alternativa do grafo: API do OSM quando o Overpass falha

Status: aceita (2026-11-17).

## Contexto

O grafo viário vem de `ox.graph_from_place(lugar, network_type="drive")`, que consulta o Overpass (ver [001](001-cache-do-grafo.md)). Sem grafo não há pesos, Dijkstra nem rota. O cache em disco só ajuda depois do primeiro download bem-sucedido.

## Problema

O Overpass é intermitente nesta máquina. Observado (medido, não interpretado):

- 2026-11-16: `ConnectTimeout` do `requests` em 3 execuções seguidas e em 6 tentativas com 1 minuto de intervalo; `curl` a `overpass-api.de/api/status` falhou no handshake TLS (status 000); `overpass.kumi.systems` e `overpass.private.coffee` também 000; `overpass.openstreetmap.fr` 403; `maps.mail.ru` 504. Por isso 4 medições com dados reais de Messejana ficaram "não medido".
- 2026-11-17, `curl -m 15`: `overpass-api.de/api/status` 000 (em 0,64 s), `overpass.kumi.systems` 000 (15 s), `overpass.private.coffee` 000 (15 s); `nominatim.openstreetmap.org/status` 200 (0,15 s) e `api.openstreetmap.org/api/capabilities` 200 (0,96 s).
- Mesmo dia, pelo `osmnx`: quatro downloads cronometrados pelo Overpass FUNCIONARAM (85,7; 84,8; 95,2 e 106,0 s) e depois duas chamadas falharam com `ConnectTimeout` (`connect timeout=180`) em `overpass-api.de:443`. Ou seja, não é "sempre falha": é intermitente, e o `curl` ao `/api/status` falhou enquanto o `osmnx` conseguia baixar (não investigamos por quê).

## Causa

**Hipótese, não confirmada:** algo na rede desta máquina (ou do provedor) bloqueia ou atrasa a conexão a esses hosts do Overpass, de forma intermitente. O que foi observado: a falha ocorre na conexão (timeout/handshake TLS), antes de qualquer resposta HTTP do Overpass, enquanto Nominatim e a API do OSM respondem 200 da mesma máquina. Não testamos DNS, proxy, firewall, nem outra rede; portanto não sabemos se é bloqueio, rota ou carga do servidor.

## Decisão

`carregar_grafo` tenta o Overpass; se `ox.graph_from_place` levantar `requests.exceptions.RequestException` ou `osmnx._errors.ResponseStatusCodeError` (rede ou servidor), registra um aviso (`logging`, logger `tonton`) e chama `baixar_via_api_osm(lugar)`. Qualquer outra exceção (erro de programação, lugar inexistente) NÃO é capturada. A fonte fica em `G.graph["fonte"]` (`"overpass"` ou `"api-osm"`) e vai junto no `.graphml`. Cache, gravação atômica e "só grafo bruto" não mudam.

`baixar_via_api_osm` repete o `graph_from_place` do osmnx 2.x com outra origem dos dados:

1. Nominatim (`geocode_to_gdf`) dá o polígono; buffer de 500 m (como o osmnx faz); bbox do buffer.
2. `GET https://api.openstreetmap.org/api/0.6/map?bbox=...` com `User-Agent: tonton/0.1 (https://github.com/Guilherme-Martins-Dev/mapa-rota-tonton)` (a política de uso do OSM pede identificação) e timeout (`ox.settings.requests_timeout`).
3. Filtro dos ways com a regra do `network_type="drive"` (a API devolve footway, cycleway, etc.). As regras são lidas do filtro Overpass da própria versão instalada do osmnx (`_get_network_filter("drive")`), não copiadas à mão, e aplicadas em Python com `re.search` (a regex da Overpass não é ancorada; tag ausente passa nos `!~`). Descartam-se relações e nós que nenhum way mantido usa.
4. `ox.graph_from_xml(simplify=False, retain_all=True)`, e então, na ordem do `graph_from_polygon`: recorte pelo buffer, maior componente fraca, simplificação, recorte pelo polígono, maior componente fraca, `street_count`.

Descoberta durante a implementação (ajuste do desenho): a caixa de Messejana tem área pequena (bem abaixo de 0,25 grau²), mas a API recusou o bbox com 400 "You requested too many nodes (limit is 50000)" mesmo sem buffer, porque conta TODOS os nós (prédios, calçadas...). Por isso `_baixar_bbox` divide o bbox em quartos quando recebe 400, até 3 níveis, e une as respostas por id. Em Messejana foram 21 pedidos GET (1 + 4 + 16): 5 recusados e 16 aceitos. Área acima de 0,25 grau² levanta `ValueError` sem tentar.

## Alternativas

- Espelhos do Overpass: testados em 2026-11-16 e 2026-11-17, falharam (000, 403 ou 504).
- Extrato da Geofabrik (`.osm.pbf` do estado): pesado para baixar e ler só por causa de um bairro; não medimos o tamanho.
- Ladrilhar a API em grade fixa para áreas grandes: complexo; fica fora. **Ressalva importante, assumida aqui:** a versão inicial desta decisão previa não ladrilhar nada, mas a divisão adaptativa por quartos (bisecção) É um ladrilhamento, só que reativo. Ela foi necessária porque a API recusa (400) mais de 50.000 nós por pedido, e a caixa de Messejana, mesmo pequena em área, tinha 270.687 nós (prédios, calçadas...). Isso só apareceu na implementação, ao testar com dados reais. Continua valendo que NÃO se ladrilha área acima de 0,25 grau² (erro claro) e a divisão só reage ao 400, até 3 níveis.
- PBF + osmium (recorte local): exige instalar ferramenta nativa e baixar o PBF; não testado.

## Consequências e riscos

- Limites da API: bbox até 0,25 grau² e 50.000 nós por pedido; acima do primeiro, erro claro; o segundo é tratado por divisão do bbox em quartos (até 3 níveis; pior caso 1 + 4 + 16 + 64 = 85 pedidos, dos quais até 64 aceitos; em Messejana foram 21). Cada pedido filho espera 0,5 s antes de sair (`PAUSA_ENTRE_GETS_S`), por cortesia com a API do OSM; o primeiro pedido não espera. Cidades inteiras não cabem.
- O filtro `drive` é reaplicado em Python. Lido da versão instalada do osmnx, mas isso usa uma função privada (`_get_network_filter`) e uma leitura por regex do texto do filtro: uma versão nova do osmnx pode mudar o formato (o código levanta `RuntimeError` se não achar a regra de `highway`) ou a semântica do filtro sem aviso. Reconferir com `scripts/comparar_fontes.py` ao atualizar o osmnx.
- Os dados da API são o estado atual do OSM (como o Overpass sem `date`); as duas fontes só são comparáveis se baixadas perto uma da outra.
- A API pública tem política de uso (identificação, evitar volume): 21 pedidos por download de um bairro é razoável, mas o cache de 30 dias continua sendo o que evita repetir.
- O recorte e as etapas seguintes são os do osmnx; só os dados de entrada mudam.
- Parser de XML de fonte externa: o código usa o `xml.etree.ElementTree` da biblioteca padrão (o osmnx também). Ele não resolve entidades externas (XXE não se aplica na prática). Para a amplificação de entidades (billion laughs), a proteção vem do expat do ambiente (medido aqui: expat 2.7.4; as proteções existem nas séries 2.4 em diante, afirmação a conferir na documentação do expat, não testada por nós). A resposta vem da API do próprio OSM, não de um terceiro arbitrário, mas a alternativa mais defensiva seria `defusedxml`; não foi adotada.

## Evidência

Detalhes em [dados/comparacao-fontes-messejana.md](../dados/comparacao-fontes-messejana.md) e [dados/fumaca-real-messejana.md](../dados/fumaca-real-messejana.md). Resumo, Messejana, 2026-11-17:

- Grafo da API: 746 vértices e 1870 arestas, os mesmos números do Overpass de 2026-11-16.
- Comparação no mesmo momento (feita por um **rascunho** com 8 campos de aresta e 4 de nó; o `scripts/comparar_fontes.py` versionado, que compara todos os atributos, NÃO rodou com sucesso por `ConnectTimeout` no Overpass): mesmo conjunto de nós, mesmo `edges(keys=True)`, sem diferença nos atributos comparados.
- Tempo de download: API 46,8 a 49,6 s em 4 execuções; Overpass 85 a 106 s em 4 execuções de hoje (74 s em 2026-11-16). Dois dias, redes variáveis: indicativo, não benchmark.
- Cobertura dos testes: `tests/test_grafo_api_osm.py` (filtro `drive`, união de respostas, divisão em quartos, pausa entre pedidos, fallback só em erro de rede e fonte gravada no cache); todos sem rede.
