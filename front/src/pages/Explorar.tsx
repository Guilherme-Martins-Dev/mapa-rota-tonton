import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import { FormularioRota, type Pedido } from '../components/FormularioRota'
import { buscarRotas, ErroApi, type RotasDaApi } from '../data/api'
import { rotaDoCriterio, type Criterio } from '../data/tipos'
import { useRotas } from '../data/useRotas'
import { useFmt, useT } from '../i18n/useIdioma'
import { Metrica, SeletorCriterio, useCriterios } from '../ui'

const Mapa = lazy(() => import('../components/Mapa').then((m) => ({ default: m.Mapa })))

/** Mapa interativo: aqui o zoom e o arrasto são livres (a home é só apresentação). */
export default function Explorar() {
  const t = useT()
  const fmt = useFmt()
  const criterios = useCriterios()
  const exemplo = useRotas()
  const [criterio, setCriterio] = useState<Criterio>('tempo')
  const [resultado, setResultado] = useState<RotasDaApi | null>(null)
  const [carregando, setCarregando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const ctl = useRef<AbortController | null>(null)

  useEffect(() => () => ctl.current?.abort(), [])

  // Sem busca feita, mostra as três rotas de exemplo (GeoJSON estático); com busca, as da API.
  const rotas = resultado ?? (exemplo.estado === 'pronto' ? exemplo.rotas : null)

  const buscar = async (p: Pedido) => {
    ctl.current?.abort() // uma busca nova cancela a anterior
    const c = new AbortController()
    ctl.current = c
    setCarregando(true)
    setErro(null)
    try {
      setResultado(await buscarRotas(p.origem, p.destino, p.veiculo, c.signal))
    } catch (e) {
      if ((e as Error).name !== 'AbortError') setErro(e instanceof ErroApi && e.status === 0 ? t('erroRede') : (e as Error).message)
    } finally {
      if (ctl.current === c) setCarregando(false)
    }
  }

  return (
    <main className="explorar">
      <h1 className="sr-only">{t('explorarTitulo')}</h1>
      <Suspense fallback={null}>
        <div className="fundo">
          <Mapa rotas={rotas} criterio={criterio} interativo />
        </div>
      </Suspense>
      <aside className="painel">
        <FormularioRota carregando={carregando} erro={erro} onBuscar={buscar} />
        <SeletorCriterio valor={criterio} onChange={setCriterio} />
        <div className="metricas" aria-live="polite">
          {criterios.map((c) => {
            const r = rotaDoCriterio(rotas, c.id)
            return r ? (
              <Metrica
                key={c.id}
                valor={fmt(r.properties.distancia_km, 2)}
                unidade="km"
                rotulo={`${c.rotulo}: ${fmt(r.properties.tempo_min, 1)} min, ${fmt(r.properties.litros, 3)} L`}
                criterio={c.id}
                melhor={c.id === criterio}
              />
            ) : null
          })}
        </div>
        {exemplo.estado === 'erro' && !resultado && <p role="status">{t('exemploErro')}</p>}
        <p className="nota">
          {resultado ? t('resultadoBusca') : t('rotasExemplo')}
          {t('avisoDados')} {t('dicaZoom')}
        </p>
      </aside>
    </main>
  )
}
