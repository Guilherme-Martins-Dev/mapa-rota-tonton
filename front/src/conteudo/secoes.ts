export interface Secao {
  id: string
  titulo: string
  texto: string
}

/** Texto da narrativa; a Fase 5 troca pelo conteúdo final. */
export const SECOES: Secao[] = [
  { id: 'grafo', titulo: 'As ruas viram um grafo', texto: 'Cruzamentos são vértices; trechos de rua são arestas.' },
  { id: 'tempo', titulo: 'Tempo = comprimento / velocidade', texto: 'O trânsito da TomTom muda o peso de cada aresta.' },
  { id: 'rotas', titulo: 'Três critérios, três rotas', texto: 'Distância, tempo e consumo escolhem caminhos diferentes.' },
]
