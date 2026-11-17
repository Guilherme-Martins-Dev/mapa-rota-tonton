---
name: fluxo-pr
description: Fluxo de branch, commit, push e PR do projeto (uma etapa por PR, repo público, push via gh). Use ao publicar uma etapa ou qualquer mudança.
---

## Regras
- Uma etapa = uma branch `etapa/<n>-<slug>` a partir da `main` atualizada = um PR. Outras mudanças: `docs/...` ou `fix/...`.
- Nunca fazer merge nem push direto na `main`: o merge é do usuário.
- Repo **público**: conferir antes do commit que não há `.env`, `cache/`, chaves nem dados pessoais.
- Commits em português, terminando com a linha `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Corpo do PR em português (o que mudou, como testar, ajustes em relação ao quadro), terminando com `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
- Testes: `./.venv/Scripts/python.exe -m pytest -q` verde antes de publicar.

## Push (evita travar)
O Git Credential Manager pode abrir uma janela que o agente não consegue responder, e o push fica pendurado. Use o login do `gh`:

```
GIT_TERMINAL_PROMPT=0 git -c credential.helper= -c "credential.helper=!gh auth git-credential" push -u origin <branch>
gh pr create --base main --head <branch> --title "..." --body "..."
```

Se o push passar de ~1 minuto, não esperar: cancelar e avisar o usuário.
