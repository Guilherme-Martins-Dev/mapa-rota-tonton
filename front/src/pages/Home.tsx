import { useGSAP } from '@gsap/react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { lazy, Suspense, useRef } from 'react'
import { Link } from 'react-router-dom'
import { progresso } from '../cena/progresso'
import { HERO } from '../conteudo/secoes'
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
          <h1>{HERO.titulo}</h1>
          <p>{HERO.texto}</p>
        </div>
        <div className="acoes entra">
          <Link to="/mapa" className="botao">Explorar o mapa</Link>
          <a href="#viagem" className="link">Ver como funciona</a>
        </div>
      </section>

      <Viagem rotas={rotas} />

      <footer className="rodape">
        <p>
          Dados de ruas © colaboradores do OpenStreetMap (ODbL). Mapa base © CARTO. Amostra de veículos: Car3DB (MIT).
          Carro: "Toyota Corola" de danieljorge435 (Sketchfab, CC BY 4.0), obtido pelo MeshFleet, redimensionado e reorientado. Trânsito simulado; a TomTom não foi consultada. <Link to="/construcao" className="link">Fontes e licenças completas</Link>.
        </p>
      </footer>
    </main>
  )
}
