# Arquitetura do front

```
src/
  data/        contrato com o back-end: tipos.ts (RotaProps, validação, rotaDoCriterio), useRotas.ts
  conteudo/    textos da narrativa (secoes.ts); a Fase 5 os substitui
  components/  Mapa (deck.gl + MapLibre), Cena3D (R3F); ambos carregados com React.lazy
  ui/          design system (Cartao, Metrica, SeletorCriterio, Botao)
  tokens.css   única fonte de cor, tipo, espaço e movimento
  cores.ts     lê as cores de critério dos tokens para deck.gl/three
public/data/   rotas.geojson gerado por `python -m tonton ... --geojson`
```

Regras
- O contrato é `RotaProps` (espelha `planejador.geojson`); `carregarRotas` descarta GeoJSON fora do contrato.
- Dependências pesadas (deck.gl, maplibre, three) só entram por `import()` dinâmico.
- Cor nunca é literal fora de `tokens.css`.
- Estado de página fica em `App`; componentes de cena recebem props, sem estado global até haver necessidade (Zustand entra na Fase 4 se o scroll precisar dirigir mapa e 3D).

Validação de APIs: o `context7` exige login e não foi usado; a conferência das versões (deck.gl 9, react-map-gl 8 em `/maplibre`, R3F 9) vem do build e do `tsc`. Refazer com context7 quando autenticado.
