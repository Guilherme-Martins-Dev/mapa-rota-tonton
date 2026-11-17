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
| 3 | Dijkstra à mão, menor tempo | a fazer |
| 4 | Menor consumo de combustível | a fazer |
| 5 | Planejador: menor distância / tempo / consumo, CLI, GeoJSON | a fazer |
| front | Interface gráfica (framework a escolher pelo usuário) | depois do back-end |

## Requisitos por etapa (do quadro e do analisar.md)
- **1:** identificar o trecho da rua, o ponto do meio, e recomeçar a partir da próxima aresta (cruzamento).
- **2:** tempo = comprimento / velocidade; dois pesos (livre e atual); ~300 trechos de vias principais consultados na TomTom.
- **3:** criar as trajetórias e escolher a de menor tempo (guloso/Dijkstra com relaxamento).
- **4:** trajeto de menor consumo: litros = comprimento × f(v), f em formato de U (alto em trânsito lento, mínimo ~60-70 km/h, sobe em alta), parâmetros por veículo; usa `v_atual`.
- **5:** sistema que escolhe entre (1) menor distância, (2) menor tempo, (3) menor consumo; saída GeoJSON para o futuro front.

## Pendências conhecidas
- Etapa 2: falta cache em disco com validade (hoje o cache é só em memória) e fallback pelo `maxspeed`/padrão por tipo de via quando a TomTom falha (hoje `v_atual = v_livre`).
- Itens ilegíveis do quadro (ver `quadro-modelagem`): confirmar com o usuário se importam.
- Escolha do framework do front: decisão do usuário.
