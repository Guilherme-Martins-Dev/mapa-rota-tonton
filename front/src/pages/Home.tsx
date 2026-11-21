import { useGSAP } from '@gsap/react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { lazy, Suspense, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { progresso, viagem } from '../cena/progresso'
import { AVISO_DADOS, HERO, SECOES } from '../conteudo/secoes'
import { rotaDoCriterio, type Criterio } from '../data/tipos'
import { useRotas } from '../data/useRotas'
import { Cartao, CRITERIOS, Metrica, SeletorCriterio } from '../ui'

// Mapa (deck.gl + MapLibre) e cena 3D (three) são pesados: carregam sob demanda.
const Mapa = lazy(() => import('../components/Mapa').then((m) => ({ default: m.Mapa })))
const CenaViagem = lazy(() => import('../cena/CenaViagem').then((m) => ({ default: m.CenaViagem })))
const Cena3D = lazy(() => import('../components/Cena3D').then((m) => ({ default: m.Cena3D })))

gsap.registerPlugin(ScrollTrigger, useGSAP)

const fmt = (n: number, casas: number) => n.toFixed(casas).replace('.', ',')

export default function Home() {
  const raiz = useRef<HTMLElement>(null)
  const dados = useRotas()
  const rotas = dados.estado === 'pronto' ? dados.rotas : null
  const [criterio, setCriterio] = useState<Criterio>('tempo')
  const [pct, setPct] = useState(0) // % da viagem, em passos de 1 para não re-renderizar a cada pixel
  const rota = useMemo(() => rotaDoCriterio(rotas, criterio), [rotas, criterio])

  useGSAP(
    () => {
      if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        viagem.valor = 0.3 // sem scroll animado: a cena mostra um quadro parado no meio da rua
        setPct(30)
        return
      }
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
      // A viagem: a seção fica pinada e o scroll leva o carro da origem ao destino.
      ScrollTrigger.create({
        trigger: '#viagem',
        start: 'top top',
        end: '+=400%',
        pin: true,
        onUpdate: (st) => {
          viagem.valor = st.progress
          setPct(Math.round(st.progress * 100))
        },
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

      <section id="viagem" className="viagem" aria-labelledby="viagem-titulo">
        <div className="viagem__cena" aria-hidden="true">
          <Suspense fallback={null}>
            <CenaViagem rota={rota} />
          </Suspense>
        </div>
        <div className="viagem__texto">
          <h2 id="viagem-titulo">A mesma rota, do banco do motorista</h2>
          <p>
            O carro percorre a rota de menor tempo, com as curvas do grafo suavizadas. Os prédios ao redor são
            ilustrativos: o OpenStreetMap não traz modelos 3D deles.
          </p>
          {rota && (
            <p className="viagem__leitura">
              {fmt((pct / 100) * rota.properties.distancia_km, 2)} de {fmt(rota.properties.distancia_km, 2)} km,{' '}
              {fmt(((100 - pct) / 100) * rota.properties.tempo_min, 1)} min para chegar
            </p>
          )}
        </div>
      </section>
    </main>
  )
}
