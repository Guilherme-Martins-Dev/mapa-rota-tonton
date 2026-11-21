import { useGSAP } from '@gsap/react'
import gsap from 'gsap'
import { ScrollToPlugin } from 'gsap/ScrollToPlugin'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { lazy, Suspense, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { INTRO_VIAGEM, MERGULHO, viagem } from '../cena/progresso'
import { CAPITULOS, type Capitulo } from '../conteudo/capitulos'
import { useConteudo } from '../i18n/conteudo'
import { useFmt, useT } from '../i18n/useIdioma'
import { rotaDoCriterio, type Rotas } from '../data/tipos'
import { Metrica, useCriterios } from '../ui'
import { Tx } from '../ui/Tx'

const CenaViagem = lazy(() => import('../cena/CenaViagem').then((m) => ({ default: m.CenaViagem })))

gsap.registerPlugin(ScrollTrigger, ScrollToPlugin, useGSAP)

const N = CAPITULOS.length
/** Rolagem total da viagem, em alturas de tela: ~2 telas por capítulo, uma pergunta a cada ~0,7 tela. */
const ALTURAS = 1700

/** Capítulo que cobre o progresso p (a descida inicial conta como o primeiro). */
const capituloDe = (p: number) => Math.min(N - 1, Math.max(0, Math.floor(((p - INTRO_VIAGEM) / (1 - INTRO_VIAGEM)) * N)))
/** Progresso em que o capítulo i começa (1% depois do limite, mais que o arredondamento do pct (±0,5%), para cair dentro dele). */
const inicioDe = (i: number) => INTRO_VIAGEM + (i / N) * (1 - INTRO_VIAGEM) + 0.01

/** Posição (0..1) dentro do capítulo que cobre o progresso p. */
const fracaoDe = (p: number) => {
  const x = ((p - INTRO_VIAGEM) / (1 - INTRO_VIAGEM)) * N
  return Math.min(0.999, Math.max(0, x - Math.floor(x)))
}

/** Perguntas do professor: no scroll aparece uma por vez, conforme a posição dentro do capítulo; sem scroll (lista) aparecem todas. */
function Pergunta({ c, fracao, todas }: { c: Capitulo; fracao: number; todas?: boolean }) {
  const t = useT()
  const total = c.perguntas.length
  const i = Math.min(total - 1, Math.floor(fracao * total))
  const lista = todas ? c.perguntas : [c.perguntas[i]]
  return (
    <div className="pergunta" role="group" aria-label={t('perguntasProfessor')}>
      {lista.map((q) => (
        <div key={q.p} className="pergunta__item">
          <h4 className="pergunta__p"><Tx>{q.p}</Tx></h4>
          <p className="pergunta__r"><Tx>{q.r}</Tx></p>
        </div>
      ))}
      {!todas && total > 1 && (
        <p className="pergunta__passo" aria-hidden="true">
          {c.perguntas.map((q, k) => <span key={q.p} className={k === i ? 'pergunta__ponto pergunta__ponto--ativo' : 'pergunta__ponto'} />)}
          <span className="pergunta__contagem">{t('passo')(i + 1, total)}</span>
        </p>
      )}
    </div>
  )
}

function Painel({ c, rotas, leitura, fracao = 0, todas }: { c: Capitulo; rotas: Rotas | null; leitura?: string; fracao?: number; todas?: boolean }) {
  const t = useT()
  const fmt = useFmt()
  const criterios = useCriterios()
  return (
    <article className="capitulo">
      <h3>{c.titulo}</h3>
      <p><Tx>{c.texto}</Tx></p>
      {c.metricas && (
        <div className="capitulo__metricas">
          {criterios.map((k) => {
            const r = rotaDoCriterio(rotas, k.id)
            return r ? (
              <Metrica
                key={k.id}
                valor={fmt(r.properties.distancia_km, 2)}
                unidade="km"
                rotulo={`${k.rotulo}: ${fmt(r.properties.tempo_min, 1)} min, ${fmt(r.properties.litros, 3)} L`}
                criterio={k.id}
              />
            ) : null
          })}
        </div>
      )}
      <Pergunta c={c} fracao={fracao} todas={todas} />
      {c.acoes && (
        <div className="acoes">
          <Link to="/mapa" className="botao">{t('explorarMapa')}</Link>
          <Link to="/construcao" className="link">{t('comoConstruido')}</Link>
        </div>
      )}
      {leitura && <p className="capitulo__leitura">{leitura}</p>}
    </article>
  )
}

/**
 * A viagem: a seção fica pinada e o scroll leva o carro da largada à chegada. Cada trecho do caminho é um
 * capítulo do projeto. Com movimento reduzido não há pin: a cena fica parada e os capítulos viram uma lista.
 */
/**
 * Mergulho do hero na rua (progresso 0..MERGULHO): o carro do hero vai ao centro da tela, encolhe e se funde à cena da rua
 * que aparece por baixo, enquanto o mapa (Mapa.tsx) dá zoom e inclina até a largada. É função só do progresso: reversível.
 */
function mergulhar(prog: number) {
  const q = Math.min(1, Math.max(0, prog / MERGULHO))
  const d = q * q * (3 - 2 * q)
  const carro = document.querySelector<HTMLElement>('.cena3d')
  const rua = document.querySelector<HTMLElement>('.viagem__cena')
  if (carro) {
    const dx = window.innerWidth / 2 - (carro.offsetLeft + carro.offsetWidth / 2)
    const dy = window.innerHeight / 2 - (carro.offsetTop + carro.offsetHeight / 2)
    const sai = Math.min(1, Math.max(0, (d - 0.55) / 0.45))
    carro.style.transform = `translate3d(${dx * d}px, ${dy * d}px, 0) scale(${1 - 0.5 * d})`
    carro.style.opacity = String(1 - sai)
  }
  if (rua) rua.style.opacity = String(Math.min(1, Math.max(0, (d - 0.75) / 0.25)))
}

export function Viagem({ rotas }: { rotas: Rotas | null }) {
  const t = useT()
  const fmt = useFmt()
  const { capitulos } = useConteudo()
  const raiz = useRef<HTMLElement>(null)
  const gatilho = useRef<ScrollTrigger | null>(null)
  const [pct, setPct] = useState(0) // % da viagem, em passos de 1: o painel só re-renderiza quando muda
  const reduz = useMemo(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches, [])
  const rota = useMemo(() => rotaDoCriterio(rotas, 'tempo'), [rotas])
  const idx = capituloDe(pct / 100)

  useGSAP(
    () => {
      if (reduz) {
        viagem.valor = 0.3 // quadro parado no meio da rua
        return
      }
      gatilho.current = ScrollTrigger.create({
        trigger: raiz.current,
        start: 'top top',
        end: `+=${ALTURAS}%`,
        pin: true,
        onUpdate: (st) => {
          viagem.valor = st.progress
          mergulhar(st.progress)
          setPct(Math.round(st.progress * 100))
        },
      })
    },
    { scope: raiz, dependencies: [reduz] },
  )

  const irPara = (i: number) => {
    const st = gatilho.current
    if (!st) return
    gsap.to(window, { scrollTo: st.start + inicioDe(i) * (st.end - st.start), duration: 1.4, ease: 'power2.inOut' })
  }

  const leitura = rota
    ? t('leituraKm')(fmt((pct / 100) * rota.properties.distancia_km, 2), fmt(rota.properties.distancia_km, 2))
    : undefined

  return (
    <section id="viagem" ref={raiz} className={reduz ? 'viagem viagem--lista' : pct < MERGULHO * 100 + 1 ? 'viagem viagem--mergulho viagem--espera' : pct < INTRO_VIAGEM * 100 ? 'viagem viagem--espera' : 'viagem'} aria-labelledby="viagem-titulo">
      <h2 id="viagem-titulo" className="sr-only">{t('viagemTitulo')(N)}</h2>
      <div className="viagem__cena" aria-hidden="true">
        <Suspense fallback={null}>
          <CenaViagem rota={rota} />
        </Suspense>
      </div>
      {reduz ? (
        <div className="viagem__lista">
          {capitulos.map((c) => (
            <Painel key={c.id} c={c} rotas={rotas} todas />
          ))}
        </div>
      ) : (
        <>
          <div className="viagem__painel" aria-live="polite">
            <Painel key={capitulos[idx].id} c={capitulos[idx]} rotas={rotas} leitura={leitura} fracao={fracaoDe(pct / 100)} />
          </div>
          <nav className="viagem__capitulos" aria-label={t('capitulosNav')}>
            <ol>
              {capitulos.map((c, i) => (
                <li key={c.id}>
                  <button type="button" aria-label={`${i + 1}. ${c.rotulo}`} aria-current={i === idx ? 'step' : undefined} onClick={() => irPara(i)}>
                    <span className="viagem__num">{i + 1}</span>
                    <span className="viagem__nome">{c.rotulo}</span>
                  </button>
                </li>
              ))}
            </ol>
          </nav>
        </>
      )}
      <p className="viagem__creditos">
        {t('viagemCreditos')} <Link to="/construcao" className="link">{t('fontesLicencas')}</Link>
      </p>
    </section>
  )
}
