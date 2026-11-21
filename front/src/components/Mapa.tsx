import { TripsLayer } from '@deck.gl/geo-layers'
import { PathLayer } from '@deck.gl/layers'
import DeckGL from '@deck.gl/react'
import { setWorkerUrl } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'
import { useEffect, useMemo, useState } from 'react'
import { Map } from 'react-map-gl/maplibre'
import { progresso } from '../cena/progresso'
import { corCriterio, corRgb } from '../cores'
import { rotaDoCriterio, type Criterio, type RotaFeature, type Rotas } from '../data/tipos'

// O Vite não resolve o worker do MapLibre sozinho: aponta a URL do arquivo empacotado.
setWorkerUrl(workerUrl)

const MESSEJANA = { longitude: -38.4935, latitude: -3.8267, zoom: 14.2, pitch: 45, bearing: 0 }
const BASE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json'
const reduzMovimento = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches

/** Timestamps 0..1 proporcionais ao índice do vértice (o traço percorre a rota de ponta a ponta). */
function tempos(f: RotaFeature): number[] {
  const n = f.geometry.coordinates.length
  return f.geometry.coordinates.map((_, i) => i / Math.max(n - 1, 1))
}

export function Mapa({ rotas, criterio, interativo = false }: { rotas: Rotas | null; criterio: Criterio; interativo?: boolean }) {
  const [t, setT] = useState(0)
  // Apresentação (home): câmera travada, guiada pelo scroll. Explorar (/mapa): zoom e arrasto livres.
  const animar = !interativo && !reduzMovimento()
  // Centro da câmera = centro da caixa das rotas (cai para Messejana sem dados).
  const centro = useMemo(() => {
    const pts = rotas?.features.flatMap((f) => f.geometry.coordinates) ?? []
    if (!pts.length) return MESSEJANA
    const lons = pts.map((p) => p[0]), lats = pts.map((p) => p[1])
    return { ...MESSEJANA, longitude: (Math.min(...lons) + Math.max(...lons)) / 2, latitude: (Math.min(...lats) + Math.max(...lats)) / 2 }
  }, [rotas])
  const [vista, setVista] = useState(centro)
  useEffect(() => setVista(centro), [centro])

  // Pulso do traço + deriva de câmera guiada pelo scroll, em um único rAF.
  useEffect(() => {
    if (!animar) return
    let id = 0
    const t0 = performance.now()
    const laco = (agora: number) => {
      setT(((agora - t0) / 3000) % 1.6)
      const bearing = Math.round(progresso.valor * 400) / 10 // só atualiza a câmera quando o scroll mexe (0,1°)
      setVista((v) => (v.bearing === bearing ? v : { ...v, bearing, pitch: 45 + progresso.valor * 10 }))
      id = requestAnimationFrame(laco)
    }
    id = requestAnimationFrame(laco)
    return () => cancelAnimationFrame(id)
  }, [animar])

  const rota = useMemo(() => rotaDoCriterio(rotas, criterio), [rotas, criterio])
  const cor = corCriterio(criterio)

  const layers = rotas
    ? [
        new PathLayer<RotaFeature>({
          id: 'rotas',
          data: rotas.features,
          getPath: (f) => f.geometry.coordinates as [number, number][],
          getColor: (f) => [...cor, f === rota ? 255 : 60] as [number, number, number, number],
          updateTriggers: { getColor: [criterio, rota] },
          getWidth: 14,
          widthUnits: 'meters',
        }),
        ...(rota && animar
          ? [
              new TripsLayer<RotaFeature>({
                id: 'pulso',
                data: [rota],
                getPath: (f) => f.geometry.coordinates as [number, number][],
                getTimestamps: tempos,
                getColor: corRgb('texto'),
                widthMinPixels: 4,
                trailLength: 0.35,
                currentTime: t,
              }),
            ]
          : []),
      ]
    : []

  return (
    <DeckGL initialViewState={vista} controller={interativo} layers={layers}>
      <Map mapStyle={BASE} reuseMaps interactive={interativo} />
    </DeckGL>
  )
}
