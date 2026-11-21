export interface Secao {
  id: string
  titulo: string
  texto: string
}

/** Narrativa da home, na ordem do scroll. Os números aparecem só nos componentes, vindos do GeoJSON. */
export const SECOES: Secao[] = [
  {
    id: 'grafo',
    titulo: 'As ruas viram um grafo',
    texto: 'Cada cruzamento de Messejana é um vértice e cada trecho de rua, uma aresta com sentido. Ruas de mão única e vias paralelas entram como são.',
  },
  {
    id: 'tempo',
    titulo: 'O peso é o tempo',
    texto: 'O tempo de um trecho é o comprimento dividido pela velocidade. Com o trânsito, a velocidade muda e o mesmo trecho passa a pesar mais.',
  },
  {
    id: 'rotas',
    titulo: 'Três critérios, três rotas',
    texto: 'Menor distância, menor tempo e menor consumo de combustível raramente escolhem o mesmo caminho. Role para ver cada um.',
  },
]

export const HERO = {
  titulo: 'Messejana em três rotas',
  texto: 'Um grafo da cidade, o trânsito e o Dijkstra escolhem o caminho por distância, tempo ou combustível.',
}

export const AVISO_DADOS = 'Trânsito simulado para esta demonstração; a TomTom não foi consultada.'
