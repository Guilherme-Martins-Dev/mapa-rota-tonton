import { useGSAP } from '@gsap/react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { useEffect, useRef, useState } from 'react'
import { Cena3D } from './components/Cena3D'
import { Mapa } from './components/Mapa'
import { carregarRotas, type Rotas } from './data/tipos'

gsap.registerPlugin(ScrollTrigger, useGSAP)

const SECOES = [
  { id: 'grafo', titulo: 'As ruas viram um grafo', texto: 'Cruzamentos são vértices; trechos de rua são arestas.' },
  { id: 'tempo', titulo: 'Tempo = comprimento / velocidade', texto: 'O trânsito da TomTom muda o peso de cada aresta.' },
  { id: 'rotas', titulo: 'Três critérios, três rotas', texto: 'Distância, tempo e consumo escolhem caminhos diferentes.' },
]

export default function App() {
  const raiz = useRef<HTMLElement>(null)
  const [rotas, setRotas] = useState<Rotas | null>(null)
  useEffect(() => void carregarRotas().then(setRotas), [])

  useGSAP(
    () => {
      const reduzir = window.matchMedia('(prefers-reduced-motion: reduce)').matches
      if (reduzir) return
      gsap.utils.toArray<HTMLElement>('.secao').forEach((el) => {
        gsap.from(el.querySelector('.cartao'), {
          opacity: 0,
          y: 40,
          scrollTrigger: { trigger: el, start: 'top 70%', end: 'top 30%', scrub: true },
        })
      })
    },
    { scope: raiz },
  )

  return (
    <main ref={raiz}>
      <div className="fundo">
        <Mapa rotas={rotas} />
      </div>
      <div className="cena3d">
        <Cena3D />
      </div>
      {SECOES.map((s) => (
        <section key={s.id} id={s.id} className="secao">
          <article className="cartao">
            <h2>{s.titulo}</h2>
            <p>{s.texto}</p>
          </article>
        </section>
      ))}
    </main>
  )
}
