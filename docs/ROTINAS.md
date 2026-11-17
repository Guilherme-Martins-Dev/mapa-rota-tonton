# PRs restantes e prompts prontos para o /schedule

Cada etapa é um PR. As rotinas **abrem o PR e param**: o merge é sempre do usuário, e a etapa seguinte só começa com a anterior mergeada.

Ordem: #4 skills → #5 cache de trânsito → **etapa 3** → **etapa 4** → **etapa 5** → front (depois, com o framework escolhido).

| PR | Branch | Depende de | Entrega |
|---|---|---|---|
| 3 | `etapa/3-guloso-menor-tempo` | #4 e #5 mergeados | `rotas.py`: Dijkstra à mão, peso `t_atual`/`t_livre`/`length` |
| 4 | `etapa/4-consumo` | etapa 3 | `consumo.py`: litros = comprimento × f(v), peso `litros` |
| 5 | `etapa/5-planejador` | etapa 4 | `planejador.py` + `cli.py`: 3 critérios, GeoJSON, plot |

Os detalhes de cada etapa estão em `.claude/workflows/etapa.js` (campo `escopo`) e nas skills `roteiro-etapas` e `quadro-modelagem`.

## Como rodar cada etapa

**Localmente (recomendado, usa o `.venv`):** peça "execute a etapa N" ou rode o workflow `etapa` com `{"etapa": N}`.

**Com /schedule (ambiente remoto, sem o seu `.venv` nem `.env`):** cole o prompt abaixo. Os testes não precisam da chave TomTom (tudo é mockado), então a rotina não deve receber a `TOMTOM_KEY`.

## Prompt-base (troque N, SLUG e TITULO)

```
Repositório: Guilherme-Martins-Dev/mapa-rota-tonton (público).

Execute a ETAPA N do projeto: TITULO.

Antes de começar, confira com `gh pr list --state all` e `git log origin/main`:
- a etapa anterior (e o PR #4 de skills e o #5 de cache, se N = 3) já foi mergeada na main; se não, PARE e explique o que falta;
- não existe PR aberto para a branch etapa/N-SLUG; se existir, PARE.

Passos:
1. `git checkout main && git pull`, depois `git checkout -b etapa/N-SLUG`.
2. `python -m venv .venv`, instale `-r requirements-dev.txt` e rode `pytest -q` para ver a base verde.
3. Leia as skills em .claude/skills (roteiro-etapas, quadro-modelagem, tomtom-trafego, fluxo-pr) e docs/quadro.png.
4. Escopo da etapa: copie o campo `escopo` da etapa N em .claude/workflows/etapa.js.
5. Implemente em src/tonton/ (reaproveitando grafo.py, ruas.py, pesos.py, transito.py) e escreva testes em tests/ com grafos sintéticos. Nunca chame a TomTom nem baixe o OSM nos testes.
6. `pytest -q` verde. Revise o próprio diff contra o quadro: grafo dirigido e multi, t = comprimento/velocidade, relaxamento correto, unidades. Procure chaves no diff.
7. Atualize a tabela de status da skill roteiro-etapas.
8. Commit em português terminando com a linha "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"; push; `gh pr create --base main` com corpo em português (o que mudou, como testar, decisões) terminando com "🤖 Generated with [Claude Code](https://claude.com/claude-code)".

NÃO faça merge. Devolva a URL do PR.
```

## Valores por etapa

| N | SLUG | TITULO |
|---|---|---|
| 3 | `guloso-menor-tempo` | Dijkstra: menor tempo |
| 4 | `consumo` | Menor consumo de combustível |
| 5 | `planejador` | Planejador completo |

## Cuidados
- O repositório é público: nada de `.env`, chave TomTom ou `cache/` em commit ou descrição de PR.
- Se a rotina remota não tiver o `gh` autenticado, ela consegue commitar e dar push, mas não abrir o PR; nesse caso abra pelo link que o `git push` imprime.
- Uma etapa por execução. Para a próxima, só depois do merge.
