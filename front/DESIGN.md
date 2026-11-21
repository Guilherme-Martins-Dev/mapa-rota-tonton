# DNA visual — Rotas de Messejana

> Fase 1. Direção definida a partir do briefing (grafos + mapa + scroll + 3D). **Não houve pesquisa no Refero**: o MCP exige login (OAuth) e ainda não foi autenticado. Quando autenticar, refazer a seção "Referências" com `refero_search_styles` e ajustar os tokens.

## Tese visual
Cartografia técnica noturna: a cidade é um grafo luminoso sobre fundo escuro. A cor carrega significado (cada critério de rota tem uma cor fixa) e o resto é contido.

## design_system
| Token | Valor | Papel |
|---|---|---|
| `--fundo` | `#0a0e14` | canvas |
| `--superficie` | `#121821` | cartões |
| `--borda` | `#ffffff1f` | divisórias |
| `--texto` | `#e8edf3` | corpo |
| `--texto-suave` | `#97a3b3` | apoio |
| `--c-distancia` | `#4cc9f0` | só rota "menor distância" |
| `--c-tempo` | `#ffbe3c` | só rota "menor tempo" |
| `--c-consumo` | `#7bd88f` | só rota "menor consumo" |
| `--c-alerta` | `#ff6b6b` | trânsito lento |

Regra de papel: as três cores de critério **não** servem de decoração nem de botão; o acento de interface é o `--texto` em contorno.

Tipografia: títulos e corpo em **Instrument Sans** (600/400), uma só família; números com `tabular-nums`, sem monoespaçada. Escala 1.25 (`0.8 / 1 / 1.25 / 1.563 / 1.953 / 2.441 rem`). `text-wrap: balance` nos títulos.
Espaço: base 4 px; seções com `min-height: 100vh`. Forma: raio 12 px nos cartões, 2 px nos chips de dados. Elevação: sem sombra, só borda + desfoque de fundo.
Movimento: ease `cubic-bezier(.22,1,.36,1)`, 240–600 ms; rolagem controla a progressão (scrub); `prefers-reduced-motion` desliga.

## design_style
- Humor: preciso, calmo, de "painel de controle". Voz: direta, em português, sem jargão desnecessário; explica o grafo antes da fórmula.
- Composição: mapa em tela cheia como palco; texto em cartões estreitos à esquerda; peça 3D como acento no canto.
- Imagem: nada de fotos; dados reais (rotas, métricas) e modelos 3D estilizados low-poly em `--c-tempo`.
- Evitar: roxo/índigo, gradientes decorativos, serifa decorativa, cartões em grade genérica.

## visual_effects
- deck.gl: rotas com traço animado (TripsLayer) na Fase 4; pitch 45°.
- three/R3F: modelos `.glb` (carro, cruzamento) girando com o scroll; intensidade média, orçamento < 300 kB por modelo.
- GSAP ScrollTrigger: seções pinadas, scrub.
- Desempenho: camada 3D e mapa carregados sob demanda (`import()`).

## Referências
Pendente (Refero sem login). Candidatos de busca: "dark map data storytelling", "developer tool dark technical landing", "logistics routing product website".
