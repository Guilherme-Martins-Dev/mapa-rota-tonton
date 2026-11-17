---
name: tomtom-trafego
description: Como usar a API TomTom Traffic Flow no projeto (endpoint, parâmetros, cota, cache, fallback) e como tratar a chave. Use ao mexer em transito.py ou pesos.py e ao escrever testes que envolvam trânsito.
---

## API
- Endpoint: `https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json`.
- Parâmetros: `point=lat,lon` (sem espaço), `unit=KMPH`, `key`.
- Resposta (`flowSegmentData`): `currentSpeed` (= `v_atual`), `freeFlowSpeed` (= `v_livre`), `currentTravelTime`, `freeFlowTravelTime`.
- Já existe `tonton.transito.consultar_trafego(lat, lon)`; reutilize.

## Chave (o repositório é PÚBLICO)
- Só via `tonton.config.tomtom_key()` (`TOMTOM_KEY` no ambiente ou `.env`). Nunca em código, teste, log, commit ou descrição de PR.
- Antes de qualquer commit: `grep -rI "key=" .` e conferir que `.env` está no `.gitignore`.

## Cota
- O plano gratuito tem limite diário: consultar só vias `trunk/primary/secondary/tertiary` (~300 trechos), no ponto médio, deduplicando pontos repetidos.
- Pendente: cache em disco com validade em `cache/`, para não gastar cota a cada execução.
- Falha de rede, 403/429 ou via sem dados: não derrubar o cálculo; usar velocidade de fallback.

## Testes
- Nunca chamar a API real em pytest: `monkeypatch` em `requests.get` ou injetar a função `consultar` (como `pesos.atribuir_pesos` já aceita).
- Teste manual real (com a chave no ambiente) só fora do CI.
