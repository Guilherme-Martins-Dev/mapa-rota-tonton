/** English version of construcao.ts (same exports and ids). Keep both files in sync. */
import type { Decisao, Etapa, Fonte, Nivel, Pergunta } from './construcao'

export const NIVEIS_EN: { id: Nivel; rotulo: string }[] = [
  { id: 'basico', rotulo: 'Basic' },
  { id: 'intermediario', rotulo: 'Intermediate' },
  { id: 'avancado', rotulo: 'Advanced' },
]

export const INDICE_EN = [
  { id: 'resumo', rotulo: 'Summary' },
  { id: 'arquitetura', rotulo: 'Architecture' },
  { id: 'back', rotulo: 'Back-end' },
  { id: 'front', rotulo: 'Front-end' },
  { id: 'dados', rotulo: 'Data and licenses' },
  { id: 'limites', rotulo: 'Limits' },
  { id: 'perguntas', rotulo: 'Questions' },
  { id: 'referencias', rotulo: 'References' },
  { id: 'reproduzir', rotulo: 'Reproduce' },
] as const

export const NUMEROS_EN = [
  { valor: '746', rotulo: 'vertices in the Messejana graph' },
  { valor: '1,870', rotulo: 'directed edges' },
  { valor: '303', rotulo: 'test functions in the back-end (pytest)' },
  { valor: '5', rotulo: 'documented design decisions' },
]

export const ETAPAS_EN: Etapa[] = [
  { titulo: 'Download the map', texto: 'OSMnx asks OpenStreetMap for the streets of Messejana (Overpass API). If Overpass fails, the project uses the OSM API and splits the area into pieces.' },
  { titulo: 'Cache it', texto: 'The graph becomes a .graphml file and is only downloaded again after 30 days or on explicit request.' },
  { titulo: 'Weight the edges', texto: 'Each segment gets a distance (m), free-flow and current time (s) and fuel use (L), which depend on speed.' },
  { titulo: 'Choose the path', texto: 'Dijkstra (written by hand), A* with a haversine heuristic and Yen for alternatives, over the weight of the chosen criterion.' },
  { titulo: 'Serve it through the API', texto: 'A FastAPI service with three queries: vehicles, street names and routes between two streets, in GeoJSON.' },
  { titulo: 'Show it in the browser', texto: 'A React site with a map (deck.gl on MapLibre), a 3D scene (three.js) and scroll-driven animation.' },
]

export const DECISOES_EN: Decisao[] = [
  { doc: 'docs/decisoes/001-cache-do-grafo.md', titulo: 'On-disk graph cache', resumo: 'Downloading the graph took 74 to 106 s through Overpass (six runs over two days); with the cache the download only repeats when the file is older than 30 days.' },
  { doc: 'docs/decisoes/002-rotas-alternativas.md', titulo: 'Alternative routes (Yen) with a filter', resumo: 'Plain Yen returns near-duplicates: on the 30x30 grid the 2nd route repeats 96.4% of the optimal length. That is why there is an overlap filter (default 0.8) and a limit of 50 candidates.' },
  { doc: 'docs/decisoes/003-transito-incremental.md', titulo: 'Incremental traffic update', resumo: 'Redoing every edge on each cycle burns TomTom quota: there are 228 edges in 211 distinct midpoints. The decision describes how to update only what is worth it.' },
  { doc: 'docs/decisoes/004-fonte-alternativa-api-osm.md', titulo: 'Fallback source: the OSM API', resumo: 'The OSM API downloaded the same neighborhood in 46.8 to 49.6 s (4 runs), against 85 to 106 s for Overpass on the same day. The bbox is split because the API limits area and node count.' },
  { doc: 'docs/decisoes/005-otimizacao-yen-astar.md', titulo: 'Speeding up Yen with A*', resumo: 'For current time with k = 10, the median dropped from 827.5 ms to 147.8 ms (5.60x), without changing the result. The heuristic is admissible and consistent.' },
]

export const FRONT_TECNICAS_EN: Etapa[] = [
  { titulo: 'Map and 3D scene', texto: 'deck.gl draws the routes over MapLibre; three.js (through React Three Fiber) draws the car and the street. Both heavy libraries load on demand.' },
  { titulo: 'Scroll-driven animation', texto: 'GSAP ScrollTrigger pins the journey section and turns scroll into a 0-to-1 progress value. The car, the camera and the map are functions of that number, so everything reverses when you scroll back up.' },
  { titulo: 'The street from the real route', texto: 'The route coordinates are projected onto a plane, corners are rounded (Chaikin) and smoothed with a moving average. Buildings are drawn with a fixed seed, away from the road and without overlapping.' },
  { titulo: 'The car and its wheels', texto: 'The Corolla comes from MeshFleet. The converter separates the four wheels; they roll by the distance traveled divided by the radius and the front ones steer in curves.' },
  { titulo: 'Performance', texto: 'Off-screen canvases are paused. Measured on an Intel UHD 620 integrated GPU: 40, 36 and 49 fps in the hero, the dive and the journey; JS memory from 169 to 68 MB. Lighthouse 100/100/100 (accessibility, best practices and SEO).' },
  { titulo: 'Accessibility', texto: 'With reduced motion the journey becomes a list of chapters with no pin. There is a visible focus, keyboard navigation and the panel is an aria-live region.' },
  { titulo: 'Theme and language', texto: 'Light and dark themes share the same design tokens, and each theme has its own car color. Switching drives a car across the screen in a drift: its rear tire marks spread like ink and reveal the new theme (View Transitions with a growing clip-path), with a color fade or an instant swap as fallbacks. The site is available in Portuguese and English, and both choices are saved in the browser.' },
]

export const PILHA_EN = [
  ['Back-end', 'Python, OSMnx 2, NetworkX, FastAPI, Uvicorn, pytest'],
  ['Front-end', 'React 19, TypeScript 7, Vite 8, React Router 7'],
  ['Map', 'deck.gl 9.4, MapLibre GL 6.19, react-map-gl 8'],
  ['3D', 'three 0.187, React Three Fiber 9, drei 10, glTF-Transform 4'],
  ['Animation', 'GSAP 3.15 (ScrollTrigger) and @gsap/react'],
  ['Quality', 'oxlint, tsc, Lighthouse, project design lint'],
]

export const FONTES_EN: Fonte[] = [
  { nome: 'OpenStreetMap', uso: 'Streets, intersections, directions and speed limits', licenca: 'ODbL 1.0', nota: '© OpenStreetMap contributors; attribution is mandatory.' },
  { nome: 'CARTO (base map)', uso: 'Map background in the browser', licenca: 'CARTO terms', nota: 'Attribution shown in the corner of the map.' },
  { nome: 'TomTom Traffic Flow', uso: 'Current speed per segment on main roads', licenca: 'TomTom terms', nota: 'The code can query it (15-minute cache), but the published demo uses simulated traffic and does not call TomTom.' },
  { nome: 'Car3DB', uso: 'Data for one catalog vehicle (Golf Alltrack 2.0 TDI)', licenca: 'MIT (the sample used only)', nota: 'The other four catalog profiles are illustrative.' },
  { nome: 'MeshFleet + Sketchfab', uso: '3D car model: "Toyota Corola", by danieljorge435', licenca: 'CC BY 4.0', nota: "MeshFleet's Apache-2.0 license covers its code and metadata; each model keeps its author's license, checked on the Sketchfab API. Changes: scale, rotation, separated wheels. Details in docs/front/CREDITOS-3D.md." },
  { nome: '3DRealCar', uso: 'Evaluated and dropped', licenca: 'Apache-2.0 (dataset)', nota: 'The repository only has preprocessing code; the scans live in cloud folders. It was replaced by MeshFleet.' },
  { nome: 'LP-Sandro', uso: 'Reference for section structure and the theme transition', licenca: 'Not applicable', nota: 'Only studied. No code or file from it is in this project.' },
]

export const LIMITES_EN: string[] = [
  'The traffic shown is simulated, with a fixed seed. TomTom is not queried in the published demo.',
  'Fuel use follows a curve of the form $a + b/v + c\\,v^{2}$. The coefficients are the ones in the code and were not validated against measurements of a real car.',
  'The 3D model and the buildings along the street are a representation: buildings are drawn at random and do not match the ones in Messejana.',
  'The covered area is Messejana. A coordinate more than 1.5 km from the graph is rejected by the API.',
  'Still missing: an API rate limit, end-to-end tests and the Lighthouse CLS and TBT metrics.',
]

export const PERGUNTAS_EN: Pergunta[] = [
  // ---------- basic ----------
  { nivel: 'basico', p: 'What is a graph?', r: 'A set of vertices connected by edges. Here, each intersection is a vertex and each street segment between two intersections is an edge.' },
  { nivel: 'basico', p: 'What does the system do, in one sentence?', r: 'It takes an origin, a destination and a vehicle and returns three routes in Messejana: the shortest, the fastest and the one that uses the least fuel.' },
  { nivel: 'basico', p: 'Where does the map data come from?', r: 'From OpenStreetMap, downloaded with the OSMnx library. It is a collaborative map under the ODbL license, which requires crediting the contributors.' },
  { nivel: 'basico', p: 'Why is the graph "directed"?', r: 'Because there are one-way streets. The edge from u to v may exist without the edge from v to u, and the algorithm respects that.' },
  { nivel: 'basico', p: 'Are the three routes always different?', r: 'No. When the same path wins on all three criteria, the three coincide. For the home demo, a pair of streets where they differ was chosen.' },
  { nivel: 'basico', p: 'Is the traffic on the site real?', r: 'No. It is simulated, with a fixed seed, and the screens say so. The code can query TomTom, but the published demo does not call it.' },
  { nivel: 'basico', p: 'What languages was the project written in?', r: 'Python on the back-end (graph, weights, algorithms and API) and TypeScript with React on the site.' },
  // ---------- intermediate ----------
  { nivel: 'intermediario', p: 'How does Dijkstra work?', r: 'It keeps the best known cost to each vertex and a priority queue. It pops the lowest-cost vertex, settles that cost and tries to improve its neighbors (relaxation). It stops when the destination is settled. The code is our own, using Python\'s heapq.' },
  { nivel: 'intermediario', p: 'What is the complexity of Dijkstra here?', r: 'With a binary priority queue, $O\\big((V + E)\\log V\\big)$. For the Messejana graph, $V = 746$ and $E = 1{,}870$.' },
  { nivel: 'intermediario', p: 'Why does Dijkstra not accept negative weights?', r: 'It assumes that once a vertex is settled, no future path improves it. With a negative weight that stops being true. The code rejects negative weights instead of returning a possibly wrong route.' },
  { nivel: 'intermediario', p: 'What is A* and how does it differ from Dijkstra?', r: 'It is Dijkstra guided by an estimate $h(v)$ of the remaining cost to the destination. The queue is ordered by $g(v) + h(v)$, the cost already paid plus the estimate, so it explores fewer vertices. If $h$ is admissible and consistent, the result is the same as Dijkstra.' },
  { nivel: 'intermediario', p: 'What does Yen\'s algorithm do and why is there an overlap filter?', r: 'Yen lists the k best loopless routes in cost order, blocking segments of the best route to force detours. The k shortest often differ by a single block (on the 30x30 grid the 2nd repeats 96.4% of the optimal), so the project discards routes that overlap an accepted one by more than 80%.' },
  { nivel: 'intermediario', p: 'How is fuel use calculated?', r: 'In liters per 100 km, $L(v) = a + \\dfrac{b}{v} + c\\,v^{2}$, with $v$ in km/h. At low speed $b/v$ weighs more, at high speed $c\\,v^{2}$ does, and there is a minimum in between, at $v^{*} = \\left(\\dfrac{b}{2c}\\right)^{1/3}$. The liters for a segment are $L(v)$ times its length. Each vehicle fits the curve from city consumption (30 km/h) and highway consumption (90 km/h).' },
  { nivel: 'intermediario', p: 'Why is the shortest route not the one with the lowest fuel use?', r: 'Because consumption per kilometer depends on the segment speed. A shorter but slower path can burn more than a slightly longer, free-flowing one.' },
  { nivel: 'intermediario', p: 'Why cache the graph?', r: 'Downloading took 74 to 106 s through Overpass (measured). The .graphml file avoids repeating the download on every run; it is only rebuilt after 30 days or on request.' },
  { nivel: 'intermediario', p: 'What does the API validate?', r: 'It rejects with 422 an unknown vehicle, a nonexistent street, a point outside the area and an origin equal to the destination; it returns 404 if there is no path. A street name needs at least two characters.' },
  // ---------- advanced ----------
  { nivel: 'avancado', p: 'Why is the A* heuristic admissible and consistent?', r: 'The haversine is the shortest length on the sphere between two points, so every edge costs at least $c \\times \\mathrm{hav}(u, v)$, where $c$ is the smallest weight-to-length ratio (corrected if the length is smaller than the distance between the coordinates). With $h(v) = c \\times \\mathrm{hav}(v, \\text{destination})$ and the haversine triangle inequality, $h(u) \\le w(u, v) + h(v)$. That is consistency, which implies admissibility.' },
  { nivel: 'avancado', p: 'What if the heuristic cannot be guaranteed?', r: 'The code recomputes c by scanning all edges on every call, storing nothing in the graph (so it stays valid after a traffic update). If a coordinate is missing, a weight is negative, there is no useful edge or c is zero, it falls back to plain Dijkstra.' },
  { nivel: 'avancado', p: 'How much did A* help Yen, and with what measurement?', r: 'For current time, with k = 10, the median dropped from 827.5 ms to 147.8 ms (5.60x) by combining A*, removing an expensive pre-check repeated in every Dijkstra and other tweaks, without changing the result. The measurement and the variants are in docs/decisoes/005 and docs/dados/bench-otimizacao.md.' },
  { nivel: 'avancado', p: 'Why is Yen expensive?', r: "The project's hypothesis, not measured step by step: the 2nd route needs one Dijkstra for each vertex of the optimal route where a detour is possible, and the following routes repeat that. On the 30x30 grid, with k = 3, Yen cost about 110 times a simple search; on 60x60, about 220 times (ratios of the project's medians)." },
  { nivel: 'avancado', p: 'How does the car follow the curves of the route on the site?', r: 'The route is projected onto the plane (local equirectangular projection), rounded with Chaikin corner cutting and smoothed with a moving average. The car follows the position by distance traveled and turns toward the heading measured on a ±2-unit chord, smoothed; sharp curves become turns, not jolts. The camera follows behind with a delay.' },
  { nivel: 'avancado', p: 'How are the wheels animated?', r: 'The model ships the four wheels fused into one mesh. The converter splits them by quadrant, recenters each on its axle and creates a steering node and a rolling node. On the site, rolling advances by $\\Delta\\theta = \\Delta s / r$ each frame ($\\Delta s$ = distance traveled, $r$ = wheel radius, $0.311$) and the front wheels steer in proportion to the car\'s turn rate, capped at 0.45 rad.' },
  { nivel: 'avancado', p: 'How was the transition from the map to the street made?', r: 'In the first 10% of the pinned section progress, the map zooms from 14.2 to 17, tilts from 45° to 60° and rotates to the start heading, while the hero car moves to the center, shrinks by half and fades and the street scene appears by opacity. Everything is a function of scroll progress, so it is reversible.' },
  { nivel: 'avancado', p: 'How was performance measured and what does it not say?', r: 'I counted requestAnimationFrame frames while scrolling the page in three phases, on an Intel UHD 620 integrated GPU, with the tab in the foreground: 40, 36 and 49 fps. It is one machine, one session and no CPU throttling; it is useful to compare versions, not a guarantee for other devices. The Lighthouse used did not return the Performance score; from the trace, LCP was 525 ms on localhost.' },
  { nivel: 'avancado', p: 'What security and license care was taken?', r: "The TomTom key lives in .env, outside the (public) repository, and the demo does not use it. Each 3D model had its license checked at the source, and one model was dropped because the CSV and Sketchfab disagreed. An API rate limit is still missing." },
  { nivel: 'avancado', p: 'What would you do next?', r: 'Limit API requests, run the full Lighthouse with CLS and TBT, validate the consumption curve against real measurements, enable TomTom with a cache and use bidirectional Dijkstra or ALT to speed up Yen (both analyzed and postponed in docs/decisoes/005).' },
]

export const REFERENCIAS_EN: string[] = [
  'DIJKSTRA, E. W. A note on two problems in connexion with graphs. Numerische Mathematik, v. 1, n. 1, p. 269-271, 1959.',
  'HART, P. E.; NILSSON, N. J.; RAPHAEL, B. A formal basis for the heuristic determination of minimum cost paths. IEEE Transactions on Systems Science and Cybernetics, v. 4, n. 2, p. 100-107, 1968.',
  'YEN, J. Y. Finding the K shortest loopless paths in a network. Management Science, v. 17, n. 11, p. 712-716, 1971.',
  'CHAIKIN, G. M. An algorithm for high-speed curve generation. Computer Graphics and Image Processing, v. 3, n. 4, p. 346-349, 1974.',
  'SINNOTT, R. W. Virtues of the Haversine. Sky and Telescope, v. 68, n. 2, p. 159, 1984.',
  'BOEING, G. OSMnx: new methods for acquiring, constructing, analyzing, and visualizing complex street networks. Computers, Environment and Urban Systems, v. 65, p. 126-139, 2017.',
  'CORMEN, T. H. et al. Introduction to Algorithms. MIT Press (chapter on single-source shortest paths).',
  'BOBORZI, D. et al. MeshFleet: filtered and annotated 3D vehicle dataset for domain specific generative modeling. arXiv:2503.14002, 2025.',
  'OPENSTREETMAP CONTRIBUTORS. OpenStreetMap, Open Database License 1.0. https://www.openstreetmap.org/copyright',
]

export const COMANDOS_EN: { rotulo: string; cmd: string }[] = [
  { rotulo: 'Install the back-end', cmd: 'pip install -e .' },
  { rotulo: 'Run the tests', cmd: 'pytest' },
  { rotulo: 'Start the API', cmd: 'uvicorn tonton.api:app --app-dir src --port 8000' },
  { rotulo: 'Install and run the site', cmd: 'cd front && npm install && npm run dev' },
  { rotulo: 'Check the site', cmd: 'cd front && npm run lint && npm run build' },
  { rotulo: 'Regenerate the procedural 3D models', cmd: 'cd front && npm run modelos' },
]
