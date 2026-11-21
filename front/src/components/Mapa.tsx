import { PathLayer } from '@deck.gl/layers'
import DeckGL from '@deck.gl/react'
import 'maplibre-gl/dist/maplibre-gl.css'
import { Map } from 'react-map-gl/maplibre'
import type { Rotas } from '../data/tipos'

const MESSEJANA = { longitude: -38.4935, latitude: -3.8267, zoom: 13.5, pitch: 45 }
const BASE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json'

export function Mapa({ rotas }: { rotas: Rotas | null }) {
  const layers = rotas
    ? [
        new PathLayer({
          id: 'rotas',
          data: rotas.features,
          getPath: (f) => f.geometry.coordinates as [number, number][],
          getColor: [255, 190, 60],
          getWidth: 6,
          widthUnits: 'meters',
        }),
      ]
    : []
  return (
    <DeckGL initialViewState={MESSEJANA} controller layers={layers}>
      <Map mapStyle={BASE} reuseMaps />
    </DeckGL>
  )
}
