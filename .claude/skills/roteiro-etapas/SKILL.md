---
name: roteiro-etapas
description: Roteiro das etapas 0-5 do back-end de rotas com status, requisitos vindos do quadro e pendências. Use para saber o que já foi feito, o que falta e o que cada etapa deve entregar.
---

Atualize o status aqui no PR que concluir cada etapa. Regras de modelagem: skill `quadro-modelagem`.

| Etapa | Entrega | Status |
|---|---|---|
| 0 | Estrutura `src/tonton`, git, CI, agentes, workflow | feito (PR #1) |
| 1 | Identificar ruas: trecho, ponto médio, cruzamento seguinte, filtro de tipos, busca por nome | feito (PR #2) |
| 2 | Pesos `t_livre` e `t_atual` com TomTom | feito (PR #3), com pendências abaixo |
| 3 | Dijkstra à mão, menor tempo | feito (PR #6) |
| 4 | Menor consumo de combustível | feito (PR #7) |
| 5 | Planejador: menor distância / tempo / consumo, CLI, GeoJSON | feito (PR #8) |
| extra | Cache do grafo em disco (.graphml) e documentação inicial | feito (PR #9) |
| extra | Rotas alternativas (k melhores, Yen + filtro de sobreposição): `--alternativas K` | feito (PR a abrir) |
| front | Interface gráfica (framework a escolher pelo usuário) | depois do back-end |

## Requisitos por etapa (do quadro e do analisar.md)
- **1:** identificar o trecho da rua, o ponto do meio, e recomeçar a partir da próxima aresta (cruzamento).
- **2:** tempo = comprimento / velocidade; dois pesos (livre e atual); ~300 trechos de vias principais consultados na TomTom.
- **3:** criar as trajetórias e escolher a de menor tempo (guloso/Dijkstra com relaxamento).
- **4:** trajeto de menor consumo: litros = comprimento × f(v), f em formato de U (alto em trânsito lento, mínimo ~60-70 km/h, sobe em alta), parâmetros por veículo; usa `v_atual`.
- **5:** sistema que escolhe entre (1) menor distância, (2) menor tempo, (3) menor consumo; saída GeoJSON para o futuro front.

## Pendências conhecidas
- Etapa 2: o cache em disco com validade está no PR #5 (`transito.com_cache`). O fallback por `maxspeed`/padrão por tipo de via já existe em `pesos.velocidade_livre_osm` (sem TomTom, `v_atual = v_livre`).
- Cada PR de etapa deve atualizar a tabela de status acima.
- Ordem de merge: #4 (skills) → #5 (cache) → etapa 3 → etapa 4 → etapa 5. As etapas 3, 4 e 5 dependem da anterior mergeada.
- Itens ilegíveis do quadro (ver `quadro-modelagem`): confirmar com o usuário se importam.
- Escolha do framework do front: decisão do usuário.
