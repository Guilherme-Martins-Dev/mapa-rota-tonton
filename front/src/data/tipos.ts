import type { Feature, FeatureCollection, LineString } from 'geojson'

/** Espelha `planejador.geojson` / `geojson_colecao` (src/tonton/planejador.py). */
export type Criterio = 'distancia' | 'tempo' | 'consumo'

export interface RotaProps {
  criterio: Criterio
  distancia_km: number
  tempo_min: number
  litros: number
  /** 0 = rota ótima; presente quando há alternativas (Yen). */
  indice?: number
}

export type RotaFeature = Feature<LineString, RotaProps>
export type Rotas = FeatureCollection<LineString, RotaProps>

const CRITERIOS: readonly Criterio[] = ['distancia', 'tempo', 'consumo']

function ehRota(f: unknown): f is RotaFeature {
  const p = (f as RotaFeature | undefined)?.properties
  return (
    !!p &&
    CRITERIOS.includes(p.criterio) &&
    typeof p.distancia_km === 'number' &&
    typeof p.tempo_min === 'number' &&
    typeof p.litros === 'number' &&
    (f as RotaFeature).geometry?.type === 'LineString'
  )
}

/** Confere que um JSON qualquer segue o contrato de rotas (usado também pela API). */
export function ehRotas(json: unknown): json is Rotas {
  const f = (json as Rotas | undefined)?.features
  return Array.isArray(f) && f.length > 0 && f.every(ehRota)
}

/** Carrega e valida o GeoJSON; devolve null se faltar ou vier fora do contrato. */
export async function carregarRotas(url = '/data/rotas.geojson'): Promise<Rotas | null> {
  try {
    const r = await fetch(url)
    if (!r.ok) return null
    const json = (await r.json()) as Rotas
    return Array.isArray(json.features) && json.features.every(ehRota) ? json : null
  } catch {
    return null
  }
}

/** Melhor rota (índice 0 ou a primeira) de um critério. */
export function rotaDoCriterio(rotas: Rotas | null, criterio: Criterio): RotaFeature | undefined {
  const doCriterio = rotas?.features.filter((f) => f.properties.criterio === criterio) ?? []
  return doCriterio.find((f) => (f.properties.indice ?? 0) === 0) ?? doCriterio[0]
}
