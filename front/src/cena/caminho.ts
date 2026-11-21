/** Geometria da viagem: a rota do GeoJSON vira um caminho suave no plano XZ (norte = -Z), sem React nem three. */

export type Ponto = [number, number]

/** Unidades de cena por metro: uma rota de ~3,5 km vira ~600 unidades (o carro tem ~2). */
export const ESCALA = 0.17

const M_POR_GRAU_LAT = 110574
const M_POR_GRAU_LON = 111320

/** [lon, lat] -> [x, z] em unidades de cena, com a origem no primeiro ponto (projeção equiretangular local). */
export function projetar(coords: readonly number[][], escala = ESCALA): Ponto[] {
  const [lon0, lat0] = coords[0]
  const k = Math.cos((lat0 * Math.PI) / 180)
  return coords.map(([lon, lat]) => [(lon - lon0) * k * M_POR_GRAU_LON * escala, -(lat - lat0) * M_POR_GRAU_LAT * escala])
}

/** Corte de cantos de Chaikin: arredonda as esquinas da rota mantendo as pontas fixas. */
export function suavizar(pts: Ponto[], iteracoes = 3): Ponto[] {
  let p = pts
  for (let it = 0; it < iteracoes; it++) {
    if (p.length < 3) return p
    const out: Ponto[] = [p[0]]
    for (let i = 0; i < p.length - 1; i++) {
      const [ax, az] = p[i], [bx, bz] = p[i + 1]
      out.push([0.75 * ax + 0.25 * bx, 0.75 * az + 0.25 * bz], [0.25 * ax + 0.75 * bx, 0.25 * az + 0.75 * bz])
    }
    out.push(p[p.length - 1])
    p = out
  }
  return p
}

export interface Amostra {
  x: number
  z: number
  /** tangente unitária (sentido da viagem) */
  tx: number
  tz: number
}

/** Caminho reamostrado a passo fixo: `em(s)` dá posição e tangente na distância `s` percorrida. */
export class Caminho {
  readonly comprimento: number
  readonly passo: number
  readonly amostras: Amostra[]

  constructor(pts: Ponto[], passo = 1) {
    this.passo = passo
    const acum = [0]
    for (let i = 1; i < pts.length; i++) acum.push(acum[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    this.comprimento = acum[acum.length - 1]
    const n = Math.max(2, Math.floor(this.comprimento / passo) + 1)
    const brutos: Ponto[] = []
    let j = 0
    for (let k = 0; k < n; k++) {
      const s = Math.min(k * passo, this.comprimento)
      while (j < acum.length - 2 && acum[j + 1] < s) j++
      const seg = acum[j + 1] - acum[j] || 1
      const u = (s - acum[j]) / seg
      brutos.push([pts[j][0] + (pts[j + 1][0] - pts[j][0]) * u, pts[j][1] + (pts[j + 1][1] - pts[j][1]) * u])
    }
    this.amostras = brutos.map(([x, z], i) => {
      const a = brutos[Math.max(0, i - 1)], b = brutos[Math.min(brutos.length - 1, i + 1)]
      const d = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1
      return { x, z, tx: (b[0] - a[0]) / d, tz: (b[1] - a[1]) / d }
    })
  }

  /** Posição e tangente em `s` (limitado a [0, comprimento]); interpola entre amostras. */
  em(s: number): Amostra {
    const f = Math.min(Math.max(s, 0), this.comprimento) / this.passo
    const i = Math.min(Math.floor(f), this.amostras.length - 2)
    const u = f - i
    const a = this.amostras[i], b = this.amostras[i + 1]
    const tx = a.tx + (b.tx - a.tx) * u, tz = a.tz + (b.tz - a.tz) * u
    const d = Math.hypot(tx, tz) || 1
    return { x: a.x + (b.x - a.x) * u, z: a.z + (b.z - a.z) * u, tx: tx / d, tz: tz / d }
  }
}

/** Gerador pseudoaleatório determinístico (mulberry32): a mesma rota gera sempre o mesmo bairro. */
export function aleatorio(semente: number): () => number {
  let a = semente >>> 0
  return () => {
    a = (a + 0x6d2b79f5) >>> 0
    let t = a
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

export type TipoPredio = 'predio' | 'torre' | 'comercio' | 'casa' | 'medio'

export interface Predio {
  tipo: TipoPredio
  x: number
  z: number
  /** rotação em Y: a fachada (+Z do modelo) fica virada para a rua */
  rotY: number
  escala: number
  /** distância percorrida (s) do ponto da rua mais próximo, para carregar só os vizinhos do carro */
  s: number
}

/** Peso de cada tipo: muito prédio médio e casa, pouca torre (bairro, não centro financeiro). */
const SORTEIO: [TipoPredio, number][] = [['casa', 0.28], ['comercio', 0.22], ['medio', 0.22], ['predio', 0.18], ['torre', 0.1]]

/** Raio de cada pegada (80% da meia-diagonal W×D do modelo, em unidades de cena), para não sobrepor prédios largos. */
const RAIO: Record<TipoPredio, number> = { predio: 2.4, torre: 3.1, comercio: 3.1, casa: 2.0, medio: 2.4 }

export interface OpcoesPredios {
  /** meia-largura da pista mais calçada: o centro do prédio fica a este valor da linha central */
  recuo?: number
  /** espaçamento entre candidatos ao longo da rua */
  passo?: number
  /** vão mínimo entre as pegadas de dois prédios */
  folga?: number
  semente?: number
}

/**
 * Põe prédios dos dois lados da rua. Descarta candidatos que caem em cima da pista (lado de dentro de curvas
 * fechadas) ou em cima de outro prédio, então nenhum prédio invade a rua.
 */
export function distribuirPredios(rua: Caminho, { recuo = 6, passo = 4.6, folga = 0.4, semente = 7 }: OpcoesPredios = {}): Predio[] {
  const rnd = aleatorio(semente)
  const colocados: Predio[] = []
  const guia = rua.amostras.filter((_, i) => i % 2 === 0) // 1 ponto a cada 2 unidades basta para medir a distância à pista
  for (let s = passo; s < rua.comprimento - passo; s += passo) {
    const c = rua.em(s)
    for (const lado of [-1, 1]) {
      const sorteio = rnd(), jitter = (rnd() - 0.5) * 1.6, escala = 0.62 + rnd() * 0.24, folgaLado = rnd() * 1.2
      const nx = -c.tz * lado, nz = c.tx * lado // normal do lado escolhido
      const x = c.x + nx * (recuo + folgaLado) + c.tx * jitter, z = c.z + nz * (recuo + folgaLado) + c.tz * jitter
      if (guia.some((g) => Math.hypot(g.x - x, g.z - z) < recuo - 1.2)) continue // em cima da pista (curva fechada)
      let acum = 0
      let tipo = SORTEIO[0][0]
      for (const [t, peso] of SORTEIO) {
        acum += peso
        if (sorteio < acum) {
          tipo = t
          break
        }
      }
      const r = RAIO[tipo] * escala
      if (colocados.some((p) => Math.hypot(p.x - x, p.z - z) < r + RAIO[p.tipo] * p.escala + folga)) continue // em cima de outro prédio
      colocados.push({ tipo, x, z, rotY: Math.atan2(-nx, -nz), escala, s })
    }
  }
  return colocados
}

/** Média móvel sobre as amostras (pontas fixas): tira os cotovelos que o corte de cantos não resolve. */
function alisar(rua: Caminho, raio: number): Ponto[] {
  const a = rua.amostras
  return a.map((_, i) => {
    const r = Math.min(raio, i, a.length - 1 - i) // janela encolhe perto das pontas para não puxá-las
    let x = 0, z = 0
    for (let k = i - r; k <= i + r; k++) { x += a[k].x; z += a[k].z }
    const n = 2 * r + 1
    return [x / n, z / n] as Ponto
  })
}

/** Rota do GeoJSON -> caminho pronto para dirigir: projeta, arredonda esquinas e alisa. */
export function criarCaminho(coords: readonly number[][]): Caminho {
  const base = new Caminho(suavizar(projetar(coords)))
  return new Caminho(alisar(base, 5))
}
