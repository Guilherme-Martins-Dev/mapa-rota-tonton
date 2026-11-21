# Plano do front (scrollytelling de rotas)

Stack: React + TypeScript + Vite, deck.gl + MapLibre (mapa/rotas), GSAP ScrollTrigger (rolagem), react-three-fiber + drei (modelos 3D .glb).

## Decisões a fechar (padrão proposto)
- **Dados:** GeoJSON estático pré-calculado pelo back-end (`python -m tonton ... --geojson`), copiado para `front/public/data/`. Sem API no início; FastAPI só se quiser rota ao vivo.
- **Mapa base:** MapLibre + deck.gl (sem chave paga).
- **Narrativa:** scroll conta o caso Messejana: grafo → pesos de tempo → trânsito → consumo → 3 critérios → alternativas (Yen).

## Fases (status)
| Fase | Skills | Entrega | Status |
|---|---|---|---|
| 0 Correção estrutural | web-design-guidelines | Scaffold Vite+TS limpo, lint, a11y básica | feito (branch front/fase-0-scaffold) |
| 1 Branding e DNA | design-dna, refero | `DESIGN.md`: paleta, tipografia, tom | feito, sem Refero (login pendente) |
| 2 Design system | refactoring-ui, 21st, taste, hallmark | Tokens + componentes base | pendente |
| 3 Arquitetura | context7, serena | Estrutura de pastas, loader de GeoJSON, tipos | pendente |
| 4 Cena e scrollytelling | build-threejs-scroll-worlds, react-three-fiber, shader-dev, gsap-scrolltrigger | Seções pinadas + deck.gl animado | pendente |
| 5 Conteúdo e páginas | context7 | Textos das seções, página de método | pendente |
| 6 Refino de movimento | emil-design-eng, motion-design, review-animations | Easing, reduced-motion | pendente |
| 7 Validação e publicação | chrome-devtools-mcp, playwright, web-design-guidelines, security-guidance | Lighthouse, e2e, deploy | pendente |

## Regras de economia de contexto
- Cada fase em branch `front/fase-N-...` e PR próprio; ao fechar, atualizar a coluna Status.
- Saídas grandes (Lighthouse, logs) vão para arquivo e são lidas com grep/ctx_search.
- Navegação de código com Serena (símbolos), não leitura de arquivo inteiro.
