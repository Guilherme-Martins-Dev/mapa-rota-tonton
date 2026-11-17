# 001. Cache em disco do grafo viário

Status: aceita (2026-11-16).

## Contexto

O projeto modela Messejana como um grafo dirigido e múltiplo (vértices = cruzamentos, arestas = trechos de rua) obtido do OpenStreetMap com `ox.graph_from_place(..., network_type="drive")`. Todo o resto (pesos, Dijkstra, CLI) parte desse grafo.

## Problema

Cada execução baixava o OSM de novo. Medido em Messejana: **74,5 s** só para ter o grafo, contra **0,12 s** lendo um arquivo local. Os cálculos seguintes (pesos e três rotas) levam menos de 0,02 s: quase todo o tempo de uma consulta era o download.

## Causa

**Para o Overpass: hipótese parcialmente medida.** Em 2026-11-16 só o total tinha sido medido (74,5 s para baixar contra 0,12 s para ler o arquivo). Em 2026-11-17, numa execução com cronômetros nas funções do osmnx (106,0 s de total, dia mais lento), o pedido ao Overpass (`_overpass_request`) levou 104,07 s, cerca de 98% do total; geocodificar, simplificar, maior componente e comprimentos somaram cerca de 2 s. Isso é UMA execução e não separa rede de processamento no servidor; o cProfile (rede contra Python) NÃO foi medido porque o Overpass falhou com `ConnectTimeout` nas duas tentativas. Seguimos tratando "o tempo está na espera do Overpass" como hipótese bem apoiada, não confirmada. Ver [dados/fumaca-real-messejana.md](../dados/fumaca-real-messejana.md).

Na fonte alternativa (API do OSM, [decisão 004](004-fonte-alternativa-api-osm.md)) o download levou 46,8 a 49,6 s em 4 execuções, 84,5% no GET do XML (39,90 s de 47,23 s) e 11,7% no filtro em Python; isso é outra fonte e NÃO é comparável com os 74,5 s.

As etapas que o download percorre são estas (ordem do código do osmnx, sem tempos):

1. Pedido ao serviço público Overpass, compartilhado e às vezes lotado (numa de nossas tentativas respondeu 502): rede e processamento no servidor.
2. Parsing do JSON recebido.
3. Construção do grafo, simplificação da topologia e cálculo de comprimentos.

Ler o `.graphml` pula todas elas: só faz o parsing de um XML de 0,80 MB já simplificado. Nas medições acima o pedido de rede domina o download nas duas fontes.

## Decisão

`carregar_grafo(lugar, usar_cache=True, validade_dias=30, pasta=CACHE)` guarda o grafo em `cache/grafo-<slug do lugar>.graphml`.

- Se o arquivo existe e tem menos de `validade_dias`, é lido. Se não existe, venceu ou está corrompido (qualquer exceção ao ler), baixa e regrava.
- A gravação é atômica: escreve em `.tmp` e faz `replace`, então uma queda no meio nunca deixa um arquivo pela metade.
- Só o grafo bruto do OSM é gravado. Pesos (`t_livre`, `t_atual`, `litros`) são calculados depois, a cada execução.
- `usar_cache=False` na função e `--atualizar-grafo` na CLI forçam novo download e regravam o arquivo.

## Alternativas descartadas

- Sempre baixar: simples, mas 74,5 s por execução e dependência de um serviço público instável.
- `pickle`: carregar um pickle pode executar código arbitrário (inseguro se o arquivo for trocado) e o formato é frágil entre versões de Python, NetworkX e osmnx. Não medimos velocidade do pickle.
- GeoPackage (`ox.save_graph_geopackage`): bom para SIG, mas grava tabelas de vértices e arestas, não o grafo; reconstruir o `MultiDiGraph` dá trabalho. Não foi necessário.
- Cachear o grafo já com pesos: descartado, ver consequências.

## Consequências e riscos

- Grafo desatualizado: o OSM muda (mão única nova, rua fechada). A validade de 30 dias limita o atraso e `--atualizar-grafo` o elimina sob demanda. Ao mudar o lugar, o slug muda e o cache é outro.
- Pesos nunca vão ao cache: dependem de trânsito, veículo e fórmulas, que mudam muito mais rápido que a rede. Gravar pesos misturaria dados de épocas diferentes e esconderia erros de fórmula.
- O ida-e-volta preserva os tipos de que o código depende (ver evidência), mas isso é propriedade do osmnx 2.1.2; o script de fumaça serve para conferir de novo ao atualizar a biblioteca.
- A pasta `cache/` está no `.gitignore`: o arquivo não vai para o repositório.

## Evidência

Medido por `scripts/fumaca_real.py` (detalhes em [dados/fumaca-real-messejana.md](../dados/fumaca-real-messejana.md)), Messejana, 746 vértices e 1870 arestas:

| Etapa | Tempo |
|---|---|
| Download sem cache (+ gravar) | 74,5 s (outra execução: 74,0 s) |
| Leitura do .graphml | 0,12 s |
| `preparar_grafo` sem trânsito | < 0,01 s |
| 3 rotas | 0,01 s |

Tipos após o ida-e-volta (contagem de tipos Python): `length` float, `geometry` LineString, `highway`/`name`/`maxspeed` str ou list. Executadas em 2026-11-17: a comparação aresta a aresta entre grafo baixado e grafo lido deu 0 diferenças (746 e 746 nós, 1870 e 1870 `edges(keys=True)`) e 0 valores str começando com `[`, tanto com o download pelo Overpass quanto pela API do OSM.
