# 003. Atualização incremental do trânsito

Status: aceita (2026-11-17).

## Contexto

Os pesos de tempo (`t_livre`, `t_atual`) e o consumo (`litros`) dependem da velocidade que a TomTom informa por trecho. Hoje `pesos.atribuir_pesos` e `consumo.atribuir_consumo` refazem todas as arestas e consultam todos os pontos médios das vias principais (Messejana: 228 arestas TomTom em 211 pontos médios distintos, medido em [dados/fumaca-real-messejana.md](../dados/fumaca-real-messejana.md)). O trânsito muda com o tempo; o refresh precisa se repetir.

## Problema

Repetir o refresh completo a cada ciclo gasta cota da API e tempo de espera, mesmo quando quase nada mudou. Queremos atualizar só o que vale a pena e saber, sem rodar o Dijkstra, quando uma rota já calculada continua a melhor.

## Causa

Premissa verificada com medição, não assumida: **o custo está na rede, não no cálculo**. Medido com `scripts/bench_transito.py` (resultados e ambiente em [dados/bench-transito.md](../dados/bench-transito.md)):

- **(a) CPU, em grafo sintético** de porte parecido com Messejana (756 nós, 1881 arestas, 230 arestas TomTom em 224 pontos distintos; não é Messejana): recálculo completo (pesos + consumo) 15,8 ms; `menor_rota` 3,1 ms (mediana entre 20 pares).
- **(b) Latência real da TomTom**, 8 consultas sequenciais em pontos de Messejana: mediana 466 ms (mín 393, máx 591), todas com sucesso.
- **Extrapolação, não medida:** 211 consultas em sequência dariam cerca de 98 s (faixa 83 a 125 s), supondo latência constante, sem limite de taxa e sem falhas.

Ou seja, a rede custa da ordem de milhares de vezes o cálculo (98 s contra 15,8 ms, a primeira cifra extrapolada). Dijkstra e recálculo de pesos são ms; consultar menos é onde há economia, e recalcular só o que mudou é um ganho menor e secundário.

## Decisão

Novo módulo `src/tonton/atualizacao.py`, reaproveitando `pesos.py`, `consumo.py` e `ruas.py`:

- Refatoração sem mudar comportamento: `pesos.gravar_velocidades(dados, v_livre, v_atual)` e `consumo.gravar_litros(dados, veiculo)` gravam numa aresta o que antes estava dentro dos laços de `atribuir_pesos` / `atribuir_consumo`, que agora as chamam.
- `indexar(G) -> Indice`: `arestas_por_ponto` (só arestas `eh_tomtom`, agrupadas pelo `ponto_medio`) e `ultima` (instante da última consulta bem-sucedida de cada ponto; 0 = nunca).
- `atualizar_transito(G, indice, consultar, veiculo, orcamento, tolerancia_kmh, agora) -> Resultado`:
  - escolhe os pontos por `ultima` crescente (nunca consultados primeiro), no máximo `orcamento` (`None` = todos): uma cota por ciclo distribuída em rodízio, os mais velhos primeiro;
  - **falha** (exceção ou resposta incompleta): a aresta **mantém o último valor conhecido**, a falha é contada e `ultima` não avança (o ponto volta ao começo da fila). Não se grava o fallback do OSM por cima: ele é uma estimativa sem trânsito, e trocá-lo por um dado real recente faria a rota "esquecer" um congestionamento por causa de um erro de rede passageiro;
  - só reescreve a aresta se `v_livre` ou `v_atual` mudarem por `tolerancia_kmh` ou mais (padrão 1 km/h); então chama `gravar_velocidades` e `gravar_litros`. `ultima` avança mesmo sem reescrita (a consulta deu certo);
  - não muda nada além dos atributos das arestas alteradas (e `indice.ultima`).
- `Resultado` (frozen): `consultados`, `falhas`, `alteradas`, `pioraram`, `melhoraram` (subconjuntos de `alteradas` pela variação de `t_atual`), `pulados_por_orcamento` e, **acréscimo ao desenho**, `anteriores` (valores antigos de `t_livre`, `t_atual` e `litros` de cada aresta alterada).
- `rota_continua_otima(G, rota, resultado, peso) -> bool`, conservadora: `False` se alguma aresta da rota foi alterada ou se alguma aresta de fora **melhorou no próprio `peso`**; `True` caso contrário. Prova curta (pesos não negativos, rota ótima antes): se nenhuma aresta da rota mudou, seu custo é o mesmo `C`; qualquer outra rota custava `>= C` e, se as arestas alteradas fora dela só pioraram ou ficaram iguais, custa agora `>=` o que custava, logo `>= C`. A rota segue ótima (pode haver empate). Para `length`, que não muda com o trânsito, é sempre `True`.

## Alternativas descartadas

- **Recalcular tudo a cada ciclo:** é o que existe hoje. Como a rede domina (ver Causa), o custo se repete a cada ciclo para quase nenhum ganho quando poucos trechos mudaram.
- **Algoritmos dinâmicos de caminho mínimo (Ramalingam-Reps e afins):** mantêm a árvore de caminhos mínimos e consertam só a parte afetada por uma mudança de peso. Aqui não compensam: com o Dijkstra em ~3 ms no grafo sintético de porte similar, não há custo de cálculo a economizar que justifique a complexidade (estruturas extras, casos de aumento e de redução de peso, mais bugs possíveis). Argumento vale para este porte e esta medição; num grafo muito maior ou com muitas consultas por segundo teria de ser reavaliado (não medido).
- **Consultar tudo em paralelo:** reduziria o tempo de espera, mas não a cota da API, que é o limite diário do plano gratuito; e a taxa aceita pela TomTom em paralelo não foi medida. Fica como possível complemento, não substituto.

## Consequências e riscos

- **Dados com idades diferentes:** com `orcamento`, o grafo mistura trechos atualizados agora e trechos de ciclos anteriores. Uma rota pode somar velocidades de momentos distintos. `indice.ultima` dá a idade de cada ponto; o planejador ainda não a usa.
- **Falha mantém o valor antigo:** um ponto que falha sempre (via sem dados, 403) fica no topo da fila e consome parte do `orcamento` de todo ciclo sem nunca ser atualizado. Não tratado; hipótese de mitigação: contar tentativas e rebaixar o ponto (não implementado). Arestas nunca consultadas ficam com o que já tinham (o fallback do OSM, se `atribuir_pesos` rodou antes sem `consultar`; sem nenhum peso gravado, o Dijkstra as trata como inexistentes).
- **Orçamento por ciclo:** com `orcamento = n`, um refresh completo leva `ceil(pontos / n)` ciclos. Rodízio sem prioridade por importância da via.
- **Tolerância:** mudanças abaixo de 1 km/h (padrão, escolhido por nós, não calibrado) são ignoradas, então o grafo pode ficar até quase 1 km/h defasado por aresta; mudanças pequenas e repetidas na mesma direção não acumulam, pois a comparação é sempre com o valor gravado. Com `tolerancia_kmh = 0` toda consulta bem-sucedida reescreve a aresta.
- **`rota_continua_otima` é conservadora e exige a rota ótima antes:** vale só para o `Resultado` da atualização imediatamente anterior e para uma rota que era ótima. Em mudanças aleatórias, ela quase nunca confirma (ver Evidência); serve melhor com atualizações pequenas ou quando o trânsito só piora.
- **`t_livre` e `litros` também variam:** o desenho previa `True` sempre para `t_livre`; mantivemos a regra geral por peso, porque `v_livre` vem da TomTom e pode mudar (obras, por exemplo), e `litros` não é monótono em `t_atual` (curva em U). Por isso `Resultado.anteriores`.
- **Concorrência:** nada protege o grafo de leituras durante a atualização; não considerado.
- **Latência real:** extrapolada de 8 consultas, uma máquina, uma sessão.

## Evidência

Tudo em [dados/bench-transito.md](../dados/bench-transito.md); script `scripts/bench_transito.py`, semente 42, Python 3.11.15. Grafo sintético, **não é Messejana**; `consultar` falso e instantâneo (só CPU).

| operação (mediana) | tempo |
|---|---|
| recálculo completo (pesos + consumo, todas as arestas) | 15,8 ms |
| incremental, 5% dos pontos alterados (11 arestas) | 2,7 ms |
| incremental, 20% (46 arestas) | 2,9 ms |
| incremental, 100% (230 arestas) | 3,5 ms |
| `menor_rota` | 3,1 ms |
| `rota_continua_otima` | 2,4 us |

O incremental fica abaixo do completo mesmo com 100% dos pontos alterados. Hipótese, não isolada: o completo recalcula todas as 1881 arestas e o `ponto_medio` (geometria) de cada aresta TomTom a cada vez, enquanto o incremental usa o índice já montado; o benchmark não separa essas parcelas. De todo modo, são milissegundos, bem abaixo de uma única consulta de rede (466 ms de mediana).

**Rede (real):** 8 consultas, 8 sucessos, mediana 466 ms, mín 393 ms, máx 591 ms. Extrapolação (não medida) para 211 pontos: cerca de 98 s. Com 5% dos pontos (11 consultas) a mesma extrapolação daria cerca de 5 s; o refresh por orçamento troca tempo por defasagem.

**Conferência contra o Dijkstra:** em 100 pares origem-destino por linha, com `rota_continua_otima = True` o Dijkstra refeito confirmou o mesmo custo em todos os casos (26 de 26 com 1% dos pontos alterados, para `t_atual` e para `litros`). Com 5% e 20% a função devolveu `False` nos 100 casos (a rota tem ~45 arestas e, com variação aleatória que melhora metade dos trechos alterados, quase sempre alguma aresta de fora melhora ou alguma da rota muda). A conferência valida a correção (em 600 casos, 52 deram `True`, e todos os 52 foram confirmados pelo Dijkstra: nenhum falso `True`), não a utilidade em dados reais, que não foi medida.
