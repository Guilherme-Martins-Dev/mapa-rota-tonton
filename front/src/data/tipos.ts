import type { Feature, FeatureCollection, LineString } from 'geojson'

/** Propriedades que `planejador.geojson` grava em cada rota (ver src/tonton/planejador.py). */
export type Criterio = 'distancia' | 'tempo' | 'consumo'
export type RotaFeature = Feature<LineString, Record<string, unknown>>
export type Rotas = FeatureCollection<LineString, Record<string, unknown>>

export async function carregarRotas(url = '/data/rotas.geojson'): Promise<Rotas | null> {
  try {
    const r = await fetch(url)
    return r.ok ? ((await r.json()) as Rotas) : null
  } catch {
    return null
  }
}
