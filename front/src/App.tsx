import { useGSAP } from '@gsap/react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { lazy, Suspense, useMemo, useRef, useState } from 'react'
import { progresso } from './cena/progresso'
import { SECOES } from './conteudo/secoes'
import { rotaDoCriterio, type Criterio } from './data/tipos'
import { useRotas } from './data/useRotas'
import { Cartao, CRITERIOS, Metrica, SeletorCriterio } from './ui'

// Mapa (deck.gl + MapLibre) e cena 3D (three) são pesados: carregam sob demanda.
const Mapa = lazy(() => import('./components/Mapa').then((m) => ({ default: m.Mapa })))
const Cena3D = lazy(() => import('./components/Cena3D').then((m) => ({ default: m.Cena3D })))

gsap.registerPlugin(ScrollTrigger, useGSAP)

export default function App() {
  const raiz = useRef<HTMLElement>(null)
  const dados = useRotas()
  const rotas = dados.estado === 'pronto' ? dados.rotas : null
  const [criterio, setCriterio] = useState<Criterio>('tempo')
  const rota = useMemo(() => rotaDoCriterio(rotas, criterio), [rotas, criterio])

  useGSAP(
    () => {
      if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
      ScrollTrigger.create({ trigger: raiz.current, start: 'top top', end: 'bottom bottom', onUpdate: (st) => (progresso.valor = st.progress) })
      // Seção das rotas fica pinada: o scroll percorre os três critérios em sequência.
      ScrollTrigger.create({
        trigger: '#rotas',
        start: 'top top',
        end: '+=150%',
        pin: true,
        onUpdate: (st) => setCriterio(CRITERIOS[Math.min(CRITERIOS.length - 1, Math.floor(st.progress * CRITERIOS.length))].id),
      })
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
      <Suspense fallback={null}>
        <div className="fundo">
          <Mapa rotas={rotas} criterio={criterio} />
        </div>
        <div className="cena3d">
          <Cena3D />
        </div>
      </Suspense>
      {SECOES.map((s) => (
        <section key={s.id} id={s.id} className="secao">
          <Cartao titulo={s.titulo}>{s.texto}</Cartao>
          {s.id === 'rotas' && (
            <>
              <SeletorCriterio valor={criterio} onChange={setCriterio} />
              {rota && (
                <Metrica
                  valor={rota.properties.distancia_km.toFixed(2).replace('.', ',')}
                  unidade="km"
                  rotulo={`${rota.properties.tempo_min.toFixed(1).replace('.', ',')} min, ${rota.properties.litros.toFixed(2).replace('.', ',')} L`}
                  criterio={criterio}
                  melhor
                />
              )}
              {dados.estado === 'erro' && <p role="status">Não foi possível carregar as rotas.</p>}
            </>
          )}
        </section>
      ))}
    </main>
  )
}
