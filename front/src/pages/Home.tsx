import { useGSAP } from '@gsap/react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { lazy, Suspense, useRef } from 'react'
import { Link } from 'react-router-dom'
import { progresso } from '../cena/progresso'
import { useT } from '../i18n/useIdioma'
import { useRotas } from '../data/useRotas'
import { Viagem } from './Viagem'

// Mapa (deck.gl + MapLibre) e cena 3D (three) são pesados: carregam sob demanda.
const Mapa = lazy(() => import('../components/Mapa').then((m) => ({ default: m.Mapa })))
const Cena3D = lazy(() => import('../components/Cena3D').then((m) => ({ default: m.Cena3D })))

gsap.registerPlugin(ScrollTrigger, useGSAP)

/**
 * Home: o hero ("Messejana em três rotas") com o mapa travado e o carro; ao rolar, o carro desce até a largada
 * da rota e a viagem pelo projeto começa (ver Viagem.tsx).
 */
export default function Home() {
  const t = useT()
  const raiz = useRef<HTMLElement>(null)
  const dados = useRotas()
  const rotas = dados.estado === 'pronto' ? dados.rotas : null

  useGSAP(
    () => {
      if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
      // Durante o hero o scroll gira o carro e a câmera do mapa.
      ScrollTrigger.create({
        trigger: '#inicio',
        start: 'top top',
        end: 'bottom top',
        onUpdate: (st) => (progresso.valor = st.progress),
      })
      gsap.from('#inicio .cartao, #inicio .entra', { opacity: 0, y: 24, stagger: 0.08, ease: 'power3.out', duration: 0.6 })
    },
    { scope: raiz },
  )

  return (
    <main ref={raiz}>
      {/* Suspense por dentro dos contêineres: o GSAP precisa achar .cena3d no DOM logo na montagem */}
      <div className="fundo">
        <Suspense fallback={null}>
          <Mapa rotas={rotas} criterio="tempo" />
        </Suspense>
      </div>
      <div className="cena3d">
        <Suspense fallback={null}>
          <Cena3D />
        </Suspense>
      </div>

      <section id="inicio" className="secao">
        <div className="cartao">
          <h1>{t('heroTitulo')}</h1>
          <p>{t('heroTexto')}</p>
        </div>
        <div className="acoes entra">
          <Link to="/mapa" className="botao">{t('explorarMapa')}</Link>
          <a href="#viagem" className="botao botao--contorno">{t('verComoFunciona')} <span className="botao__seta" aria-hidden="true">↓</span></a>
        </div>
      </section>

      <Viagem rotas={rotas} />

    </main>
  )
}
