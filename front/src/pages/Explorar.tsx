import { lazy, Suspense, useState } from 'react'
import { AVISO_DADOS } from '../conteudo/secoes'
import { rotaDoCriterio, type Criterio } from '../data/tipos'
import { useRotas } from '../data/useRotas'
import { CRITERIOS, Metrica, SeletorCriterio } from '../ui'

const Mapa = lazy(() => import('../components/Mapa').then((m) => ({ default: m.Mapa })))

const fmt = (n: number, casas: number) => n.toFixed(casas).replace('.', ',')

/** Mapa interativo: aqui o zoom e o arrasto são livres (a home é só apresentação). */
export default function Explorar() {
  const dados = useRotas()
  const rotas = dados.estado === 'pronto' ? dados.rotas : null
  const [criterio, setCriterio] = useState<Criterio>('tempo')

  return (
    <main className="explorar">
      <h1 className="sr-only">Explorar as rotas de Messejana</h1>
      <Suspense fallback={null}>
        <div className="fundo">
          <Mapa rotas={rotas} criterio={criterio} interativo />
        </div>
      </Suspense>
      <aside className="painel">
        <SeletorCriterio valor={criterio} onChange={setCriterio} />
        <div className="metricas">
          {CRITERIOS.map((c) => {
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
        {dados.estado === 'erro' && <p role="status">Não foi possível carregar as rotas.</p>}
        <p className="nota">{AVISO_DADOS} Arraste e use a roda para dar zoom.</p>
      </aside>
    </main>
  )
}
