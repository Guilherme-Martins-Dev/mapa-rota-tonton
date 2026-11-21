/**
 * Conteúdo da página /construcao: como o projeto foi feito, com fontes, licenças e perguntas e respostas.
 * Cada afirmação vem do código (src/tonton, front/), dos documentos em docs/ (medições feitas pelo projeto)
 * ou de uma referência listada em REFERENCIAS. Onde algo não foi medido ou validado, o texto diz isso.
 */
export type Nivel = 'basico' | 'intermediario' | 'avancado'

export interface Pergunta {
  nivel: Nivel
  p: string
  r: string
}

export interface Etapa {
  titulo: string
  texto: string
}

export interface Decisao {
  doc: string
  titulo: string
  resumo: string
}

export interface Fonte {
  nome: string
  uso: string
  licenca: string
  /** o que o projeto fez com ela */
  nota?: string
}

export const NIVEIS: { id: Nivel; rotulo: string }[] = [
  { id: 'basico', rotulo: 'Básico' },
  { id: 'intermediario', rotulo: 'Intermediário' },
  { id: 'avancado', rotulo: 'Avançado' },
]

export const INDICE = [
  { id: 'resumo', rotulo: 'Resumo' },
  { id: 'arquitetura', rotulo: 'Arquitetura' },
  { id: 'back', rotulo: 'Back-end' },
  { id: 'front', rotulo: 'Front-end' },
  { id: 'dados', rotulo: 'Dados e licenças' },
  { id: 'limites', rotulo: 'Limites' },
  { id: 'perguntas', rotulo: 'Perguntas' },
  { id: 'referencias', rotulo: 'Referências' },
  { id: 'reproduzir', rotulo: 'Reproduzir' },
] as const

export const NUMEROS = [
  { valor: '746', rotulo: 'vértices no grafo de Messejana' },
  { valor: '1.870', rotulo: 'arestas dirigidas' },
  { valor: '303', rotulo: 'funções de teste no back-end (pytest)' },
  { valor: '5', rotulo: 'decisões de projeto documentadas' },
]

export const ETAPAS: Etapa[] = [
  { titulo: 'Baixar o mapa', texto: 'O OSMnx pede ao OpenStreetMap as ruas de Messejana (Overpass API). Se a Overpass falha, o projeto usa a API do OSM e divide a área em pedaços.' },
  { titulo: 'Guardar em cache', texto: 'O grafo vira um arquivo .graphml e só é baixado de novo depois de 30 dias ou por pedido explícito.' },
  { titulo: 'Dar pesos às arestas', texto: 'Cada trecho recebe distância (m), tempo livre e tempo atual (s) e consumo (L), que dependem da velocidade.' },
  { titulo: 'Escolher o caminho', texto: 'Dijkstra (escrito à mão), A* com heurística haversine e Yen para alternativas, sobre o peso do critério escolhido.' },
  { titulo: 'Servir pela API', texto: 'Uma API FastAPI com três consultas: veículos, nomes de ruas e rotas entre duas ruas, em GeoJSON.' },
  { titulo: 'Mostrar no navegador', texto: 'Um site React com mapa (deck.gl sobre MapLibre), cena 3D (three.js) e animação guiada pelo scroll.' },
]

export const DECISOES: Decisao[] = [
  { doc: 'docs/decisoes/001-cache-do-grafo.md', titulo: 'Cache em disco do grafo', resumo: 'Baixar o grafo levou de 74 a 106 s pela Overpass (seis execuções em dois dias); com o cache o download só se repete quando o arquivo passa de 30 dias.' },
  { doc: 'docs/decisoes/002-rotas-alternativas.md', titulo: 'Rotas alternativas (Yen) com filtro', resumo: 'O Yen puro devolve quase-duplicatas: na grade 30x30 a 2ª rota repete 96,4% do comprimento da ótima. Por isso há um filtro de sobreposição (padrão 0,8) e um limite de 50 candidatas.' },
  { doc: 'docs/decisoes/003-transito-incremental.md', titulo: 'Atualização incremental do trânsito', resumo: 'Refazer todas as arestas a cada ciclo gasta cota da TomTom: são 228 arestas em 211 pontos médios distintos. A decisão descreve como atualizar só o que vale a pena.' },
  { doc: 'docs/decisoes/004-fonte-alternativa-api-osm.md', titulo: 'Fonte alternativa: API do OSM', resumo: 'A API do OSM baixou o mesmo bairro em 46,8 a 49,6 s (4 execuções), contra 85 a 106 s da Overpass no mesmo dia. O bbox é dividido porque a API limita a área e o número de nós.' },
  { doc: 'docs/decisoes/005-otimizacao-yen-astar.md', titulo: 'Otimização do Yen com A*', resumo: 'Para o tempo atual com k = 10, a mediana caiu de 827,5 ms para 147,8 ms (5,60x), sem mudar o resultado. A heurística é admissível e consistente.' },
]

export const FRONT_TECNICAS: Etapa[] = [
  { titulo: 'Mapa e cena 3D', texto: 'deck.gl desenha as rotas sobre o MapLibre; three.js (via React Three Fiber) desenha o carro e a rua. As duas bibliotecas pesadas carregam sob demanda.' },
  { titulo: 'Animação guiada pelo scroll', texto: 'O GSAP ScrollTrigger prende a seção da viagem e converte o scroll em um progresso de 0 a 1. O carro, a câmera e o mapa são funções desse número, então tudo volta ao rolar para cima.' },
  { titulo: 'A rua a partir da rota real', texto: 'As coordenadas da rota são projetadas num plano, os cantos são arredondados (Chaikin) e alisados por média móvel. Os prédios são sorteados com semente fixa, longe da pista e sem se sobrepor.' },
  { titulo: 'O carro e as rodas', texto: 'O Corolla vem do MeshFleet. O conversor separa as quatro rodas; elas rolam pela distância percorrida dividida pelo raio e as dianteiras esterçam nas curvas.' },
  { titulo: 'Desempenho', texto: 'Canvases fora da tela são pausados. Medido numa GPU integrada Intel UHD 620: 40, 36 e 49 fps no hero, no mergulho e na viagem; memória de JS de 169 para 68 MB. Lighthouse 100/100/100 (acessibilidade, boas práticas e SEO).' },
  { titulo: 'Acessibilidade', texto: 'Com movimento reduzido a viagem vira uma lista de capítulos sem pin. Há foco visível, navegação por teclado e o painel é uma região aria-live.' },
]

export const PILHA = [
  ['Back-end', 'Python, OSMnx 2, NetworkX, FastAPI, Uvicorn, pytest'],
  ['Front-end', 'React 19, TypeScript 7, Vite 8, React Router 7'],
  ['Mapa', 'deck.gl 9.4, MapLibre GL 6.19, react-map-gl 8'],
  ['3D', 'three 0.187, React Three Fiber 9, drei 10, glTF-Transform 4'],
  ['Animação', 'GSAP 3.15 (ScrollTrigger) e @gsap/react'],
  ['Qualidade', 'oxlint, tsc, Lighthouse, lint de design do projeto'],
]

export const FONTES: Fonte[] = [
  { nome: 'OpenStreetMap', uso: 'Ruas, cruzamentos, sentidos e limites de velocidade', licenca: 'ODbL 1.0', nota: '© colaboradores do OpenStreetMap; obrigatório citar.' },
  { nome: 'CARTO (mapa base)', uso: 'Fundo do mapa no navegador', licenca: 'Termos da CARTO', nota: 'Atribuição exibida no canto do mapa.' },
  { nome: 'TomTom Traffic Flow', uso: 'Velocidade atual por trecho nas vias principais', licenca: 'Termos da TomTom', nota: 'O código sabe consultar (cache de 15 min), mas a demonstração publicada usa trânsito simulado e não chama a TomTom.' },
  { nome: 'Car3DB', uso: 'Dados de um veículo do catálogo (Golf Alltrack 2.0 TDI)', licenca: 'MIT (somente a amostra usada)', nota: 'Os outros quatro perfis do catálogo são ilustrativos.' },
  { nome: 'MeshFleet + Sketchfab', uso: 'Modelo 3D do carro: "Toyota Corola", de danieljorge435', licenca: 'CC BY 4.0', nota: 'A licença Apache-2.0 do MeshFleet cobre o código e os metadados dele; cada modelo mantém a licença do autor, conferida na API do Sketchfab. Alterações: escala, giro, rodas separadas. Detalhes em docs/front/CREDITOS-3D.md.' },
  { nome: '3DRealCar', uso: 'Avaliado e descartado', licenca: 'Apache-2.0 (dataset)', nota: 'O repositório só traz código de pré-processamento; os scans ficam em pastas de nuvem. Foi substituído pelo MeshFleet.' },
  { nome: 'LP-Sandro', uso: 'Referência de estrutura de seções e de transição de tema', licenca: 'Não aplicável', nota: 'Foi só estudado. Nenhum código ou arquivo dele está neste projeto.' },
]

export const LIMITES: string[] = [
  'O trânsito mostrado é simulado, com semente fixa. A TomTom não é consultada na demonstração publicada.',
  'O consumo segue uma curva em forma de a + b/v + c·v². Os coeficientes são os do código e não foram validados contra medições de um carro real.',
  'O modelo 3D e os prédios da rua são uma representação: os prédios são sorteados e não correspondem aos de Messejana.',
  'A área coberta é Messejana. Uma coordenada a mais de 1,5 km do grafo é recusada pela API.',
  'Ainda faltam, na fase 7: limite de requisições na API, publicação do back-end, testes ponta a ponta e as métricas CLS e TBT do Lighthouse.',
]

export const PERGUNTAS: Pergunta[] = [
  // ---------- básico ----------
  { nivel: 'basico', p: 'O que é um grafo?', r: 'Um conjunto de vértices ligados por arestas. Aqui, cada cruzamento é um vértice e cada trecho de rua entre dois cruzamentos é uma aresta.' },
  { nivel: 'basico', p: 'O que o sistema faz, em uma frase?', r: 'Recebe uma origem, um destino e um veículo e devolve três rotas em Messejana: a de menor distância, a de menor tempo e a de menor consumo de combustível.' },
  { nivel: 'basico', p: 'De onde vêm os dados do mapa?', r: 'Do OpenStreetMap, baixados com a biblioteca OSMnx. É um mapa colaborativo com licença ODbL, que exige citar os colaboradores.' },
  { nivel: 'basico', p: 'Por que o grafo é "dirigido"?', r: 'Porque há ruas de mão única. Pode existir a aresta de u para v sem existir a de v para u, e o algoritmo respeita isso.' },
  { nivel: 'basico', p: 'As três rotas são sempre diferentes?', r: 'Não. Quando o mesmo caminho vence nos três critérios, as três coincidem. Para a demonstração da home foi escolhido um par de ruas em que elas diferem.' },
  { nivel: 'basico', p: 'O trânsito do site é real?', r: 'Não. É simulado, com semente fixa, e isso está avisado nas telas. O código sabe consultar a TomTom, mas a demonstração publicada não a chama.' },
  { nivel: 'basico', p: 'Em que linguagens o projeto foi feito?', r: 'Python no back-end (grafo, pesos, algoritmos e API) e TypeScript com React no site.' },
  // ---------- intermediário ----------
  { nivel: 'intermediario', p: 'Como o Dijkstra funciona?', r: 'Guarda o melhor custo conhecido até cada vértice e uma fila de prioridade. Tira da fila o vértice de menor custo, fixa esse custo e tenta melhorar os vizinhos (relaxamento). Termina quando o destino é fixado. O código é próprio, com heapq do Python.' },
  { nivel: 'intermediario', p: 'Qual a complexidade do Dijkstra aqui?', r: 'Com fila de prioridade binária, O((V + E) log V). Para o grafo de Messejana, V = 746 e E = 1.870.' },
  { nivel: 'intermediario', p: 'Por que o Dijkstra não aceita peso negativo?', r: 'Ele assume que, ao fixar um vértice, nenhum caminho futuro o melhora. Com peso negativo isso deixa de valer. O código recusa pesos negativos em vez de devolver uma rota possivelmente errada.' },
  { nivel: 'intermediario', p: 'O que é o A* e o que muda em relação ao Dijkstra?', r: 'É o Dijkstra guiado por uma estimativa h(v) do custo restante até o destino. A fila ordena por custo já pago mais h(v), então explora menos vértices. Se h for admissível e consistente, o resultado é o mesmo do Dijkstra.' },
  { nivel: 'intermediario', p: 'O que o algoritmo de Yen faz e por que há um filtro de sobreposição?', r: 'O Yen lista as k melhores rotas sem repetir vértices, em ordem de custo, bloqueando trechos da melhor rota para forçar desvios. As k menores costumam diferir só em um quarteirão (na grade 30x30, a 2ª repete 96,4% da ótima), então o projeto descarta rotas com mais de 80% de sobreposição com uma já aceita.' },
  { nivel: 'intermediario', p: 'Como o consumo é calculado?', r: 'Em litros por 100 km, L(v) = a + b/v + c·v², com v em km/h. Em baixa velocidade pesa b/v, em alta pesa c·v², e há um mínimo no meio, em v = (b / 2c)^(1/3). Os litros de um trecho são L(v) vezes o comprimento. Cada veículo ajusta a curva a partir do consumo urbano (30 km/h) e de estrada (90 km/h).' },
  { nivel: 'intermediario', p: 'Por que a rota mais curta não é a de menor consumo?', r: 'Porque o consumo por quilômetro depende da velocidade do trecho. Um caminho mais curto, mas lento, pode gastar mais que um um pouco mais longo e fluido.' },
  { nivel: 'intermediario', p: 'Por que guardar o grafo em cache?', r: 'Baixar levou de 74 a 106 s pela Overpass (medido). O arquivo .graphml evita repetir o download a cada execução; ele só é refeito depois de 30 dias ou por pedido.' },
  { nivel: 'intermediario', p: 'O que a API valida?', r: 'Recusa com 422 um veículo desconhecido, uma rua inexistente, um ponto fora da área e origem igual ao destino; devolve 404 se não houver caminho. O nome da rua exige pelo menos dois caracteres.' },
  // ---------- avançado ----------
  { nivel: 'avancado', p: 'Por que a heurística do A* é admissível e consistente?', r: 'A haversine é o menor comprimento sobre a esfera entre dois pontos, então toda aresta custa pelo menos c × haversine(u, v), onde c é a menor razão peso/comprimento (corrigida se o comprimento for menor que a distância entre as coordenadas). Com h(v) = c × haversine(v, destino) e a desigualdade triangular da haversine, h(u) ≤ w(u, v) + h(v). Isso é consistência, que implica admissibilidade.' },
  { nivel: 'avancado', p: 'E se não for possível garantir a heurística?', r: 'O código recalcula c varrendo todas as arestas a cada chamada, sem guardar nada no grafo (assim continua válido depois de uma atualização de trânsito). Se faltar coordenada, houver peso negativo, não houver aresta útil ou c for zero, ele volta ao Dijkstra puro.' },
  { nivel: 'avancado', p: 'Quanto o A* ajudou no Yen, e com que medição?', r: 'Para o tempo atual, com k = 10, a mediana caiu de 827,5 ms para 147,8 ms (5,60x) combinando A*, remoção de uma pré-checagem cara repetida a cada Dijkstra e outros ajustes, sem mudar o resultado. A medição e as variantes estão em docs/decisoes/005 e docs/dados/bench-otimizacao.md.' },
  { nivel: 'avancado', p: 'Por que o Yen é caro?', r: 'Hipótese do projeto, não medida etapa por etapa: a 2ª rota exige um Dijkstra para cada vértice da rota ótima onde se pode desviar, e as seguintes repetem isso. Na grade 30x30, com k = 3, o Yen custou cerca de 110 vezes a busca simples; na 60x60, cerca de 220 vezes (razões de medianas do projeto).' },
  { nivel: 'avancado', p: 'Como o carro percorre as curvas da rota no site?', r: 'A rota é projetada no plano (projeção equiretangular local), arredondada pelo corte de cantos de Chaikin e alisada por média móvel. O carro segue a posição por distância percorrida e gira para o rumo medido numa corda de ±2 unidades, suavizado; assim as curvas fechadas viram giros e não trancos. A câmera vem atrás com atraso.' },
  { nivel: 'avancado', p: 'Como as rodas são animadas?', r: 'O modelo traz as quatro rodas fundidas em uma malha. O conversor as separa por quadrante, recentra cada uma no seu eixo e cria um nó de direção e um de rolagem. No site, a rolagem avança ds / r a cada quadro (ds = distância percorrida, r = raio da roda, 0,311) e as dianteiras esterçam proporcionalmente à velocidade de giro do carro, limitado a 0,45 rad.' },
  { nivel: 'avancado', p: 'Como a passagem do mapa para a rua foi feita?', r: 'Nos primeiros 10% do progresso da seção fixada, o mapa dá zoom de 14,2 para 17, inclina de 45° para 60° e gira para o rumo da largada, enquanto o carro do hero vai ao centro, encolhe pela metade e some e a cena da rua aparece por opacidade. Tudo é função do progresso do scroll, então é reversível.' },
  { nivel: 'avancado', p: 'Como foi medido o desempenho e o que ele não diz?', r: 'Contei quadros de requestAnimationFrame rolando a página em três fases, numa GPU integrada Intel UHD 620, com a aba em primeiro plano: 40, 36 e 49 fps. É uma máquina, uma sessão e sem limitação de CPU; serve para comparar versões, não garante o mesmo em outros aparelhos. O Lighthouse usado não devolveu a nota de Performance; pelo trace, o LCP foi de 525 ms em localhost.' },
  { nivel: 'avancado', p: 'Que cuidados de segurança e de licença foram tomados?', r: 'A chave da TomTom fica em .env, fora do repositório (que é público), e a demonstração não a usa. Cada modelo 3D teve a licença conferida na fonte, e um modelo foi descartado porque o CSV e o Sketchfab divergiam. Ainda falta um limite de requisições na API, previsto para a fase 7.' },
  { nivel: 'avancado', p: 'O que você faria a seguir?', r: 'Publicar o back-end, limitar requisições, rodar o Lighthouse completo com CLS e TBT, validar a curva de consumo contra medições reais, ativar a TomTom com cache e usar Dijkstra bidirecional ou ALT para acelerar o Yen (ambos analisados e adiados em docs/decisoes/005).' },
]

export const REFERENCIAS: string[] = [
  'DIJKSTRA, E. W. A note on two problems in connexion with graphs. Numerische Mathematik, v. 1, n. 1, p. 269-271, 1959.',
  'HART, P. E.; NILSSON, N. J.; RAPHAEL, B. A formal basis for the heuristic determination of minimum cost paths. IEEE Transactions on Systems Science and Cybernetics, v. 4, n. 2, p. 100-107, 1968.',
  'YEN, J. Y. Finding the K shortest loopless paths in a network. Management Science, v. 17, n. 11, p. 712-716, 1971.',
  'CHAIKIN, G. M. An algorithm for high-speed curve generation. Computer Graphics and Image Processing, v. 3, n. 4, p. 346-349, 1974.',
  'SINNOTT, R. W. Virtues of the Haversine. Sky and Telescope, v. 68, n. 2, p. 159, 1984.',
  'BOEING, G. OSMnx: new methods for acquiring, constructing, analyzing, and visualizing complex street networks. Computers, Environment and Urban Systems, v. 65, p. 126-139, 2017.',
  'CORMEN, T. H. et al. Introduction to Algorithms. MIT Press (capítulo sobre caminhos mínimos de fonte única).',
  'BOBORZI, D. et al. MeshFleet: filtered and annotated 3D vehicle dataset for domain specific generative modeling. arXiv:2503.14002, 2025.',
  'OPENSTREETMAP CONTRIBUTORS. OpenStreetMap, licença Open Database License 1.0. https://www.openstreetmap.org/copyright',
]

export const COMANDOS: { rotulo: string; cmd: string }[] = [
  { rotulo: 'Instalar o back-end', cmd: 'pip install -e .' },
  { rotulo: 'Rodar os testes', cmd: 'pytest' },
  { rotulo: 'Subir a API', cmd: 'uvicorn tonton.api:app --app-dir src --port 8000' },
  { rotulo: 'Instalar e rodar o site', cmd: 'cd front && npm install && npm run dev' },
  { rotulo: 'Verificar o site', cmd: 'cd front && npm run lint && npm run build' },
  { rotulo: 'Regerar os modelos 3D procedurais', cmd: 'cd front && npm run modelos' },
]
