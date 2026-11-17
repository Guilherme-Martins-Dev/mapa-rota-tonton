# Documentação do projeto

Índice do que existe e do que virá. Material pensado para uso em aula.

| Documento | Conteúdo | Situação |
|---|---|---|
| [ROTINAS.md](ROTINAS.md) | Rotinas de trabalho do projeto | existe |
| [quadro.png](quadro.png) | Foto do quadro com a modelagem original | existe |
| [decisoes/001-cache-do-grafo.md](decisoes/001-cache-do-grafo.md) | Por que e como o grafo viário é guardado em disco | existe |
| [aula/faq-cache-do-grafo.md](aula/faq-cache-do-grafo.md) | Perguntas e respostas sobre o cache, na ótica de grafos | existe |
| [decisoes/002-rotas-alternativas.md](decisoes/002-rotas-alternativas.md) | Por que e como calcular as k melhores rotas (Yen) com filtro de sobreposição | existe |
| [aula/faq-rotas-alternativas.md](aula/faq-rotas-alternativas.md) | Perguntas e respostas sobre rotas alternativas, na ótica de grafos | existe |
| [dados/bench-alternativas.md](dados/bench-alternativas.md) | Benchmark em grafo sintético (grade), não Messejana; script `scripts/bench_alternativas.py` | existe |
| [decisoes/003-transito-incremental.md](decisoes/003-transito-incremental.md) | Por que e como atualizar o trânsito consultando menos e recalculando só o que mudou | existe |
| [aula/faq-transito-incremental.md](aula/faq-transito-incremental.md) | Perguntas e respostas sobre a atualização incremental, na ótica de grafos | existe |
| [dados/bench-transito.md](dados/bench-transito.md) | CPU em grafo sintético (não Messejana) e latência real da TomTom (8 consultas); script `scripts/bench_transito.py` | existe |
| [dados/fumaca-real-messejana.md](dados/fumaca-real-messejana.md) | Medições com dados reais de Messejana | existe |
| [decisoes/004-fonte-alternativa-api-osm.md](decisoes/004-fonte-alternativa-api-osm.md) | Por que e como baixar o grafo pela API do OSM quando o Overpass falha (filtro `drive` reproduzido, limites da API) | existe |
| [aula/faq-fonte-alternativa.md](aula/faq-fonte-alternativa.md) | Perguntas e respostas sobre a fonte alternativa, na ótica de grafos | existe |
| [dados/comparacao-fontes-messejana.md](dados/comparacao-fontes-messejana.md) | Overpass x API do OSM em Messejana: contagens, comprimentos, componentes, tempos; scripts `scripts/comparar_fontes.py` e `scripts/fumaca_real.py --fonte api` | existe |
| [decisoes/005-otimizacao-yen-astar.md](decisoes/005-otimizacao-yen-astar.md) | Por que e como acelerar o Yen (Lawler, A* com heurística haversine): causa medida em Messejana, candidatas aceitas e rejeitadas | existe |
| [aula/faq-otimizacao.md](aula/faq-otimizacao.md) | Perguntas e respostas sobre A*, admissibilidade, consistência e Lawler, na ótica de grafos | existe |
| [dados/bench-otimizacao.md](dados/bench-otimizacao.md) | Tempos, contagens e verificação de custos no grafo real de Messejana (trânsito simulado); script `scripts/bench_otimizacao.py` | existe |
| `decisoes/` (próximas) | Um registro por decisão técnica (contexto, problema, causa, decisão, alternativas, consequências, evidência) | virá |
| `aula/` (próximos) | Roteiros e FAQs por tema (Dijkstra, pesos, consumo) | virá |
