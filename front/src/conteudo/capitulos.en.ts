/** English version of the journey chapters (same ids and shape as capitulos.ts). Keep both files in sync. */
import type { Capitulo } from './capitulos'
import { GRAFO } from './capitulos'
import { AUTOR, COLABORADORES, CREDITOS_EN, CONTEXTO_EN, PERFIL_PROFESSOR_EN, PROFESSOR } from './equipe'

const n = (v: number) => v.toLocaleString('en-US')

export const CAPITULOS_EN: Capitulo[] = [
  {
    id: 'largada',
    rotulo: 'Start',
    titulo: 'What is the problem?',
    texto:
      'In Messejana, the shortest path is rarely the fastest, and the fastest is rarely the one that burns the least fuel. The system takes an origin and a destination and returns three routes, one for each criterion.',
    perguntas: [
      {
        p: 'What does the system return?',
        r: 'Three routes in GeoJSON, with distance (km), time (min) and fuel use (L) for the chosen vehicle.',
      },
      {
        p: 'What area does it cover?',
        r: 'The Messejana neighborhood, in Fortaleza. A coordinate more than 1.5 km from the graph is rejected by the API.',
      },
    ],
  },
  {
    id: 'grafo',
    rotulo: 'Graph',
    titulo: 'The map becomes a graph',
    texto: `Each OpenStreetMap intersection becomes a vertex and each street segment becomes a directed edge, with a length and a speed limit. Messejana has ${n(GRAFO.vertices)} vertices and ${n(GRAFO.arestas)} edges.`,
    perguntas: [
      {
        p: 'Where does the map data come from?',
        r: 'From OpenStreetMap (ODbL license), downloaded with the OSMnx library through the Overpass API. If Overpass fails, the project falls back to the OSM API, splitting the area into pieces.',
      },
      {
        p: 'Why is the graph directed?',
        r: 'Because there are one-way streets: the edge from u to v may exist without the edge from v to u.',
      },
      {
        p: 'What is a parallel edge?',
        r: 'Two distinct segments between the same vertices. The graph allows that (a multigraph), and the route uses the lighter one in each pair.',
      },
    ],
  },
  {
    id: 'pesos',
    rotulo: 'Weights',
    titulo: 'Three weights, three routes',
    texto:
      'Distance uses the edge length. Time divides the length by the street speed: $t = \\ell / v$. Fuel use converts length and speed into liters. The route is the same search with a different weight.',
    metricas: true,
    perguntas: [
      {
        p: 'Why can the three routes be the same?',
        r: 'When the same path wins on all three weights, which happens for many pairs of streets. For this demo, a pair where the three paths differ was chosen.',
      },
      {
        p: 'What if a street has no speed limit in OSM?',
        r: 'The system uses a default speed by road type, for example 50 km/h on primary roads and 30 km/h on residential streets.',
      },
    ],
  },
  {
    id: 'algoritmo',
    rotulo: 'Algorithm',
    titulo: 'How the path is chosen',
    texto:
      'Dijkstra, written by hand with a priority queue, finds the path of least weight. A* does the same with a straight-line estimate $h(v)$ to explore fewer vertices. Yen lists alternative paths.',
    perguntas: [
      {
        p: 'Why is Dijkstra correct?',
        r: 'It always settles the open vertex of lowest cost. Since no weight is negative (the code rejects negative weights), no future path can improve an already settled vertex.',
      },
      {
        p: 'Can A* be wrong?',
        r: 'No. The estimate (haversine distance times a constant) is admissible and consistent, so the final cost is the same as Dijkstra. If the code cannot guarantee that, it falls back to plain Dijkstra.',
      },
      {
        p: 'What is the complexity?',
        r: 'With a binary priority queue (heapq), $O\\big((V + E)\\log V\\big)$, where $V$ is the vertices and $E$ the edges.',
      },
      {
        p: 'What does Yen do?',
        r: 'It generates the k best loopless routes in cost order, blocking segments of the best route to force detours.',
      },
    ],
  },
  {
    id: 'consumo',
    rotulo: 'Fuel',
    titulo: 'Fuel use depends on speed',
    texto:
      'Fuel use in liters per 100 km is $L(v) = a + \\dfrac{b}{v} + c\\,v^{2}$. In slow traffic the $b/v$ term weighs more, at high speed $c\\,v^{2}$ does, and the curve has a minimum in between. Each vehicle in the catalog fits the curve from its city and highway consumption.',
    perguntas: [
      {
        p: 'Why is the shortest route not the one that uses the least fuel?',
        r: 'A short, slow segment burns more per kilometer than a longer, free-flowing one, because consumption rises at low speed.',
      },
      {
        p: 'What is the most economical speed?',
        r: 'It is $v^{*} = \\left(\\dfrac{b}{2c}\\right)^{1/3}$. On the project default curve ($a = 3.04$; $b = 150$; $c = 2.73\\cdot 10^{-4}$) that is about 65 km/h, at about 6.5 L/100 km.',
      },
      {
        p: 'Where do the vehicles come from?',
        r: "From the project's catalog: four illustrative profiles and the Golf Alltrack 2.0 TDI, from the Car3DB sample (MIT license for the sample only).",
      },
    ],
  },
  {
    id: 'transito',
    rotulo: 'Traffic',
    titulo: 'What about traffic?',
    texto: `The system can query TomTom (flow per point, in km/h, with a 15-minute cache), but only on main roads: ${n(GRAFO.arestasTomtom)} of the ${n(GRAFO.arestas)} edges. In this demo, traffic is simulated with a fixed seed and TomTom is not queried.`,
    perguntas: [
      {
        p: 'Why simulate it?',
        r: "To publish without exposing the TomTom key or spending its quota. The simulated-traffic notice appears on every screen.",
      },
      {
        p: 'How does traffic enter the weights?',
        r: "The street's current speed replaces its free-flow speed, and time and fuel use are recalculated with it.",
      },
    ],
  },
  {
    id: 'chegada',
    rotulo: 'Arrival',
    titulo: "It's your turn",
    texto:
      'Type an origin and a destination on the interactive map and compare the three routes. The sources, licenses and full answers are on the build page.',
    acoes: true,
    perguntas: [
      {
        p: 'Can I trust the times?',
        r: 'As a demo, no: traffic is simulated. The distance comes from the real OpenStreetMap graph, but time and fuel use depend on the speeds used.',
      },
    ],
  },
  {
    id: 'creditos',
    rotulo: 'Credits',
    titulo: 'Who made this project',
    texto: CREDITOS_EN,
    perguntas: [
      {
        p: 'Who did what?',
        r: `${AUTOR} developed the whole project: graph, algorithms, back-end, interface and 3D scene. ${COLABORADORES.join(', ')} collaborated on the system and helped validate the data and the results. The professor in charge is ${PROFESSOR}.`,
      },
      {
        p: 'Who is the professor in charge?',
        r: `${PERFIL_PROFESSOR_EN} ${CONTEXTO_EN}`,
      },
      {
        p: 'Where do the data and the car come from?',
        r: 'The streets come from OpenStreetMap (ODbL) and the base map is from CARTO. The catalog vehicles come from Car3DB (MIT). The 3D Toyota Corolla is by danieljorge435 (CC BY 4.0), via MeshFleet.',
      },
      {
        p: 'Where are the code and the decisions?',
        r: 'On the build page, with the architecture, the measured decisions, the sources, the licenses and the professor-style questions, from basic to advanced.',
      },
    ],
  },
]
