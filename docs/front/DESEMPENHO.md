# Desempenho e Lighthouse da home (fase 7d)

Medido em 2026-11-21 sobre `vite preview` (build de produção), Chrome com GPU integrada Intel UHD 620, janela 1440x800, aba em primeiro plano.
É uma máquina modesta e sem throttling de CPU; serve de comparação entre versões, não de garantia para outros aparelhos.

## FPS rolando a página (média de quadros por segundo, 120 passos por fase)

| Fase | Antes de pausar canvases | Depois |
|---|---|---|
| Hero (mapa + carro 3D) | 35 | 40 |
| Mergulho (mapa dá zoom, carro vai ao centro) | 35 | 36 |
| Viagem (rua 3D + capítulos) | 29 | 49 |

Memória JS: 169 MB antes, 68 MB depois. O que mudou: o canvas do carro do hero para depois do mergulho, o canvas da rua só roda quando aparece, o mapa deixa de redesenhar quando a rua o cobre e o pulso do traço atualiza a 20 Hz.

Pior quadro ainda chega a 50 a 83 ms no mergulho (mapa com zoom e a rua ao mesmo tempo). É o ponto a otimizar se algum aparelho engasgar.

## Lighthouse (navegação)

| Categoria | Celular | Desktop |
|---|---|---|
| Acessibilidade | 100 | 100 |
| Boas práticas | 100 | 100 |
| SEO | 100 | 100 |

Correções feitas a partir da primeira rodada (acessibilidade 95, SEO 82): `aria-hidden` removido do contêiner do mapa (o link de atribuição é focável), `meta description` e `robots.txt` adicionados.
A ferramenta usada não devolve a categoria Performance. Pelo trace: LCP de 525 ms (local, sem throttling). CLS e TBT não foram lidos e ficam para a rodada com Lighthouse completo.
As auditorias `llms-txt` e `ard-schema` (categoria experimental "Agentic Browsing") não se aplicam ao projeto.

Relatórios completos em `docs/front/lighthouse/`.
