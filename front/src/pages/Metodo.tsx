import { AVISO_DADOS } from '../conteudo/secoes'
import { Tx } from '../ui/Tx'

/** Página de método: o que o back-end faz, em ordem. Texto corrido, largura de leitura. */
export default function Metodo() {
  return (
    <main className="texto">
      <h1>Como as rotas são escolhidas</h1>

      <h2>O grafo</h2>
      <p>
        As ruas de Messejana vêm do OpenStreetMap. Cada cruzamento é um vértice e cada trecho entre dois cruzamentos é uma aresta.
        O grafo é dirigido, porque existem ruas de mão única, e múltiplo, porque duas ruas podem ligar os mesmos cruzamentos.
      </p>

      <h2>Um grafo, dois pesos de tempo</h2>
      <p>
        <Tx>{'O tempo de um trecho é o comprimento dividido pela velocidade, $t = \ell / v$. Guardamos dois: o tempo livre, com a velocidade da via, e o tempo atual, com a velocidade informada pela TomTom nas vias principais.'}</Tx>
      </p>

      <h2>O Dijkstra</h2>
      <p>
        <Tx>{'O Dijkstra é um algoritmo guloso com relaxamento: se chegar a $v$ passando por $u$ custa menos do que o melhor caminho conhecido até $v$, isto é, se $d[u] + w(u,v) < d[v]$, então $d[v] \leftarrow d[u] + w(u,v)$. Trocar o peso das arestas troca o critério da rota.'}</Tx>
      </p>

      <h2>Distância, tempo e consumo</h2>
      <p>
        Com o comprimento como peso, a rota é a de menor distância. Com o tempo atual, a de menor tempo. Com os litros estimados por
        trecho, a de menor consumo, que depende da velocidade em que cada trecho é percorrido.
      </p>

      <h2>Rotas alternativas</h2>
      <p>
        Para oferecer mais de uma opção, o algoritmo de Yen lista as melhores rotas em ordem de custo e descarta as que repetem
        demais o mesmo caminho. Uma busca A* com distância em linha reta como heurística acelera o cálculo sem mudar o resultado.
      </p>

      <h2>Sobre os dados desta página</h2>
      <p>{AVISO_DADOS} As rotas exibidas foram calculadas pelo back-end deste projeto sobre o grafo real de Messejana.</p>
    </main>
  )
}
