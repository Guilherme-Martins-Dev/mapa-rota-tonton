import { useGSAP } from '@gsap/react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { lazy, Suspense, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { progresso } from '../cena/progresso'
import { AVISO_DADOS, HERO, SECOES } from '../conteudo/secoes'
import { rotaDoCriterio, type Criterio } from '../data/tipos'
import { useRotas } from '../data/useRotas'
import { Cartao, CRITERIOS, Metrica, SeletorCriterio } from '../ui'

// Mapa (deck.gl + MapLibre) e cena 3D (three) são pesados: carregam sob demanda.
const Mapa = lazy(() => import('../components/Mapa').then((m) => ({ default: m.Mapa })))
const Cena3D = lazy(() => import('../components/Cena3D').then((m) => ({ default: m.Cena3D })))

gsap.registerPlugin(ScrollTrigger, useGSAP)

const fmt = (n: number, casas: number) => n.toFixed(casas).replace('.', ',')

export default function Home() {
  const raiz = useRef<HTMLElement>(null)
  const dados = useRotas()
  const rotas = dados.estado === 'pronto' ? dados.rotas : null
  const [criterio, setCriterio] = useState<Criterio>('tempo')
  const rota = useMemo(() => rotaDoCriterio(rotas, criterio), [rotas, criterio])

  useGSAP(
    () => {
      if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
      ScrollTrigger.create({
        trigger: raiz.current,
        start: 'top top',
        end: 'bottom bottom',
        onUpdate: (st) => (progresso.valor = st.progress),
      })
      // Seção das rotas fica pinada: o scroll percorre os três critérios em sequência.
      ScrollTrigger.create({
        trigger: '#rotas',
        start: 'top top',
        end: '+=150%',
        pin: true,
        onUpdate: (st) => setCriterio(CRITERIOS[Math.min(CRITERIOS.length - 1, Math.floor(st.progress * CRITERIOS.length))].id),
      })
      gsap.utils.toArray<HTMLElement>('.secao').forEach((el) => {
        gsap.from(el.querySelectorAll('.cartao, .entra'), {
          opacity: 0,
          y: 40,
          stagger: 0.08,
          ease: 'power3.out',
          scrollTrigger: { trigger: el, start: 'top 70%', end: 'top 30%', scrub: true },
        })
      })
    },
    { scope: raiz },
  )

  return (
    <main ref={raiz}>
      <Suspense fallback={null}>
        <div className="fundo" aria-hidden="true">
          <Mapa rotas={rotas} criterio={criterio} />
        </div>
        <div className="cena3d">
          <Cena3D />
        </div>
      </Suspense>

      <section id="inicio" className="secao">
        <div className="cartao">
          <h1>{HERO.titulo}</h1>
          <p>{HERO.texto}</p>
        </div>
        <div className="acoes entra">
          <Link to="/mapa" className="botao">Explorar o mapa</Link>
          <Link to="/metodo" className="link">Como funciona</Link>
        </div>
      </section>

      {SECOES.map((s) => (
        <section key={s.id} id={s.id} className="secao">
          <Cartao titulo={s.titulo}>{s.texto}</Cartao>
          {s.id === 'rotas' && (
            <>
              <SeletorCriterio valor={criterio} onChange={setCriterio} />
              {rota && (
                <Metrica
                  valor={fmt(rota.properties.distancia_km, 2)}
                  unidade="km"
                  rotulo={`${fmt(rota.properties.tempo_min, 1)} min, ${fmt(rota.properties.litros, 3)} L`}
                  criterio={criterio}
                  melhor
                />
              )}
              {dados.estado === 'erro' && <p role="status">Não foi possível carregar as rotas.</p>}
              <p className="nota">{AVISO_DADOS}</p>
            </>
          )}
        </section>
      ))}
    </main>
  )
}
