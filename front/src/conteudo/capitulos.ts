/**
 * Capítulos da viagem na home: cada trecho da rota explica uma parte do projeto.
 * Tudo aqui é afirmado a partir do código do back-end (src/tonton) ou dos dados reais do grafo de Messejana;
 * nada é estimativa. Números do grafo: `carregar_grafo()` em 2026-11-21.
 */
export interface Pergunta {
  p: string
  r: string
}

export interface Capitulo {
  id: string
  /** nome curto no seletor de capítulos */
  rotulo: string
  titulo: string
  texto: string
  /** mostra as três métricas reais da rota (só o capítulo dos pesos) */
  metricas?: boolean
  /** mostra os links finais (só o último capítulo) */
  acoes?: boolean
  perguntas: Pergunta[]
}

export const GRAFO = { vertices: 746, arestas: 1870, arestasTomtom: 228, ruasNomeadas: 196 } as const

const n = (v: number) => v.toLocaleString('pt-BR')

export const CAPITULOS: Capitulo[] = [
  {
    id: 'largada',
    rotulo: 'Largada',
    titulo: 'Qual é o problema?',
    texto:
      'Em Messejana, o caminho mais curto raramente é o mais rápido, e o mais rápido raramente é o que gasta menos combustível. O sistema recebe uma origem e um destino e devolve três rotas, uma para cada critério.',
    perguntas: [
      {
        p: 'O que o sistema entrega?',
        r: 'Três rotas em GeoJSON, com distância (km), tempo (min) e consumo (L) para o veículo escolhido.',
      },
      {
        p: 'Qual área ele cobre?',
        r: 'O bairro de Messejana, em Fortaleza. Uma coordenada a mais de 1,5 km do grafo é recusada pela API.',
      },
    ],
  },
  {
    id: 'grafo',
    rotulo: 'Grafo',
    titulo: 'O mapa vira um grafo',
    texto: `Cada cruzamento do OpenStreetMap vira um vértice e cada trecho de rua vira uma aresta direcionada, com comprimento e limite de velocidade. Em Messejana são ${n(GRAFO.vertices)} vértices e ${n(GRAFO.arestas)} arestas.`,
    perguntas: [
      {
        p: 'De onde vêm os dados do mapa?',
        r: 'Do OpenStreetMap (licença ODbL), baixados com a biblioteca OSMnx pela Overpass API. Se a Overpass falha, o projeto busca pela API do OSM, dividindo a área em pedaços.',
      },
      {
        p: 'Por que o grafo é direcionado?',
        r: 'Porque há ruas de mão única: pode existir a aresta de u para v sem existir a de v para u.',
      },
      {
        p: 'O que é uma aresta paralela?',
        r: 'Dois trechos distintos entre os mesmos vértices. O grafo permite isso (multigrafo), e a rota usa a de menor peso em cada par.',
      },
    ],
  },
  {
    id: 'pesos',
    rotulo: 'Pesos',
    titulo: 'Três pesos, três rotas',
    texto:
      'A distância usa o comprimento da aresta. O tempo divide o comprimento pela velocidade da via. O consumo converte comprimento e velocidade em litros. A rota é a mesma busca com um peso diferente.',
    metricas: true,
    perguntas: [
      {
        p: 'Por que as três rotas podem ser iguais?',
        r: 'Quando o mesmo caminho vence nos três pesos, o que acontece em muitos pares de ruas. Para esta demonstração foi escolhido um par em que os três caminhos diferem.',
      },
      {
        p: 'E se a rua não tem limite de velocidade no OSM?',
        r: 'O sistema usa uma velocidade padrão pelo tipo da via, por exemplo 50 km/h em vias primárias e 30 km/h em residenciais.',
      },
    ],
  },
  {
    id: 'algoritmo',
    rotulo: 'Algoritmo',
    titulo: 'Como o caminho é escolhido',
    texto:
      'O Dijkstra, escrito à mão com fila de prioridade, acha o caminho de menor peso. O A* faz o mesmo com uma estimativa em linha reta para explorar menos vértices. O Yen lista caminhos alternativos.',
    perguntas: [
      {
        p: 'Por que o Dijkstra acerta?',
        r: 'Ele fixa sempre o vértice aberto de menor custo. Como nenhum peso é negativo (o código recusa pesos negativos), nenhum caminho futuro melhora um vértice já fixado.',
      },
      {
        p: 'O A* pode errar?',
        r: 'Não. A estimativa (distância haversine vezes uma constante) é admissível e consistente, então o custo final é o mesmo do Dijkstra. Se o código não consegue garantir isso, ele volta ao Dijkstra puro.',
      },
      {
        p: 'Qual a complexidade?',
        r: 'Com fila de prioridade binária (heapq), O((V + E) log V), sendo V os vértices e E as arestas.',
      },
      {
        p: 'O que o Yen faz?',
        r: 'Gera as k melhores rotas sem repetir vértices, em ordem de custo, bloqueando trechos da melhor rota para forçar desvios.',
      },
    ],
  },
  {
    id: 'consumo',
    rotulo: 'Consumo',
    titulo: 'O consumo depende da velocidade',
    texto:
      'O consumo em litros por 100 km é a + b/v + c·v². Em trânsito lento pesa o termo b/v, em velocidade alta pesa c·v², e a curva tem um mínimo no meio. Cada veículo do catálogo ajusta a curva a partir do consumo urbano e de estrada.',
    perguntas: [
      {
        p: 'Por que a rota mais curta não é a que gasta menos?',
        r: 'Um trecho curto e lento gasta mais por quilômetro que um mais longo e fluido, porque o consumo sobe em baixa velocidade.',
      },
      {
        p: 'Qual a velocidade de menor consumo?',
        r: 'É v = (b / 2c)^(1/3). Na curva padrão do projeto (a = 3,04; b = 150; c = 2,73·10⁻⁴) dá cerca de 65 km/h, com cerca de 6,5 L/100 km.',
      },
      {
        p: 'De onde vêm os veículos?',
        r: 'Do catálogo do projeto: quatro perfis ilustrativos e o Golf Alltrack 2.0 TDI, da amostra do Car3DB (licença MIT só para a amostra).',
      },
    ],
  },
  {
    id: 'transito',
    rotulo: 'Trânsito',
    titulo: 'E o trânsito?',
    texto: `O sistema sabe consultar a TomTom (fluxo por ponto, em km/h, com cache de 15 minutos), mas só nas vias principais: ${n(GRAFO.arestasTomtom)} das ${n(GRAFO.arestas)} arestas. Nesta demonstração o trânsito é simulado, com semente fixa, e a TomTom não é consultada.`,
    perguntas: [
      {
        p: 'Por que simular?',
        r: 'Para publicar sem expor a chave da TomTom nem gastar a cota dela. O aviso de trânsito simulado aparece em todas as telas.',
      },
      {
        p: 'Como o trânsito entra nos pesos?',
        r: 'A velocidade atual da via substitui a velocidade livre, e o tempo e o consumo são recalculados com ela.',
      },
    ],
  },
  {
    id: 'chegada',
    rotulo: 'Chegada',
    titulo: 'Agora é com você',
    texto:
      'Digite uma origem e um destino no mapa interativo e compare as três rotas. As fontes, as licenças e as respostas completas ficam na página de construção.',
    acoes: true,
    perguntas: [
      {
        p: 'Posso confiar nos tempos?',
        r: 'Como demonstração, não: o trânsito é simulado. A distância vem do grafo real do OpenStreetMap, mas o tempo e o consumo dependem das velocidades usadas.',
      },
    ],
  },
]
