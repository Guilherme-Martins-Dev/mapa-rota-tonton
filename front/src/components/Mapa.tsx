import { TripsLayer } from '@deck.gl/geo-layers'
import { PathLayer } from '@deck.gl/layers'
import DeckGL from '@deck.gl/react'
import { setWorkerUrl } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'
import { useEffect, useMemo, useState } from 'react'
import { Map } from 'react-map-gl/maplibre'
import { MERGULHO, progresso, viagem } from '../cena/progresso'
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
    // Zoom pela maior extensão da caixa (~0,03° cabe em 14,2); viagens mais longas afastam, sem passar de 12.
    const extensao = Math.max(Math.max(...lons) - Math.min(...lons), Math.max(...lats) - Math.min(...lats))
    const zoom = Math.min(MESSEJANA.zoom, Math.max(12, MESSEJANA.zoom - Math.log2(Math.max(extensao, 0.03) / 0.03)))
    return { ...MESSEJANA, zoom, longitude: (Math.min(...lons) + Math.max(...lons)) / 2, latitude: (Math.min(...lats) + Math.max(...lats)) / 2 }
  }, [rotas])
  const [vista, setVista] = useState(centro)
  useEffect(() => setVista(centro), [centro])

  const rota = useMemo(() => rotaDoCriterio(rotas, criterio), [rotas, criterio])
  // Largada da rota e rumo inicial (graus a partir do norte): para onde o mapa mergulha no fim do hero.
  const largada = useMemo(() => {
    const c = rota?.geometry.coordinates
    if (!c || c.length < 2) return null
    const [lon0, lat0] = c[0]
    let j = 1
    while (j < c.length - 1 && Math.hypot(c[j][0] - lon0, c[j][1] - lat0) < 0.0004) j++
    const k = Math.cos((lat0 * Math.PI) / 180)
    return { longitude: lon0, latitude: lat0, bearing: (Math.atan2((c[j][0] - lon0) * k, c[j][1] - lat0) * 180) / Math.PI }
  }, [rota])

  // Pulso do traço + câmera guiada pelo scroll (deriva no hero, mergulho até a largada na viagem), em um único rAF.
  useEffect(() => {
    if (!animar) return
    let id = 0
    const t0 = performance.now()
    let ultimoPulso = 0
    const r = (x: number, f: number) => Math.round(x * f) / f
    const laco = (agora: number) => {
      if (viagem.valor > MERGULHO + 0.03) { id = requestAnimationFrame(laco); return } // a rua cobre o mapa: não redesenha
      if (agora - ultimoPulso > 50) { ultimoPulso = agora; setT(((agora - t0) / 3000) % 1.6) } // pulso lento: 20 Hz bastam e poupam o deck.gl
      const q = Math.min(1, Math.max(0, viagem.valor / MERGULHO))
      const d = q * q * (3 - 2 * q) // suavizado: o mergulho começa e termina devagar
      const b0 = progresso.valor * 40
      const dif = largada ? ((largada.bearing - b0 + 540) % 360) - 180 : 0
      const alvo = largada ?? centro
      const prox = {
        longitude: r(centro.longitude + (alvo.longitude - centro.longitude) * d, 1e5),
        latitude: r(centro.latitude + (alvo.latitude - centro.latitude) * d, 1e5),
        zoom: r(centro.zoom + (17 - centro.zoom) * d, 100),
        pitch: r(45 + progresso.valor * 10 + (60 - 45 - progresso.valor * 10) * d, 10),
        bearing: r(b0 + dif * d, 10),
      }
      setVista((v) => (v.longitude === prox.longitude && v.latitude === prox.latitude && v.zoom === prox.zoom && v.pitch === prox.pitch && v.bearing === prox.bearing ? v : { ...v, ...prox }))
      id = requestAnimationFrame(laco)
    }
    id = requestAnimationFrame(laco)
    return () => cancelAnimationFrame(id)
  }, [animar, centro, largada])

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
