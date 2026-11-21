// Codificador PNG mínimo (RGBA, sem dependências) e utilitários de textura procedural.
import { deflateSync } from 'node:zlib'

const tabela = Array.from({ length: 256 }, (_, n) => {
  let c = n
  for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1
  return c >>> 0
})
const crc = (buf) => {
  let c = 0xffffffff
  for (const b of buf) c = tabela[(c ^ b) & 255] ^ (c >>> 8)
  return (c ^ 0xffffffff) >>> 0
}
const bloco = (tipo, dados) => {
  const t = Buffer.from(tipo)
  const len = Buffer.alloc(4)
  len.writeUInt32BE(dados.length)
  const c = Buffer.alloc(4)
  c.writeUInt32BE(crc(Buffer.concat([t, dados])))
  return Buffer.concat([len, t, dados, c])
}

/** pixel(x, y) -> [r, g, b, a] (0..255). */
export function png(largura, altura, pixel) {
  const raw = Buffer.alloc((largura * 4 + 1) * altura)
  for (let y = 0; y < altura; y++) {
    raw[y * (largura * 4 + 1)] = 0
    for (let x = 0; x < largura; x++) raw.set(pixel(x, y), y * (largura * 4 + 1) + 1 + x * 4)
  }
  const ihdr = Buffer.alloc(13)
  ihdr.writeUInt32BE(largura, 0)
  ihdr.writeUInt32BE(altura, 4)
  ihdr.set([8, 6, 0, 0, 0], 8)
  return Buffer.concat([
    Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]),
    bloco('IHDR', ihdr),
    bloco('IDAT', deflateSync(raw, { level: 9 })),
    bloco('IEND', Buffer.alloc(0)),
  ])
}

/** Ruído de valor determinístico em [0, 1). */
export function ruido(x, y, semente = 1) {
  const s = Math.sin(x * 127.1 + y * 311.7 + semente * 74.7) * 43758.5453
  return s - Math.floor(s)
}

/** Ruído suave (interpolado) em [0, 1), para manchas e casca de laranja. */
export function ruidoSuave(x, y, semente = 1) {
  const x0 = Math.floor(x), y0 = Math.floor(y)
  const fx = x - x0, fy = y - y0
  const sx = fx * fx * (3 - 2 * fx), sy = fy * fy * (3 - 2 * fy)
  const a = ruido(x0, y0, semente), b = ruido(x0 + 1, y0, semente)
  const c = ruido(x0, y0 + 1, semente), d = ruido(x0 + 1, y0 + 1, semente)
  return a + (b - a) * sx + (c - a) * sy + (a - b - c + d) * sx * sy
}

/** Mapa normal (espaço tangente) a partir de um campo de alturas altura(x, y) em [0, 1]. */
export function mapaNormal(largura, altura, campo, forca = 2) {
  const h = (x, y) => campo(Math.min(largura - 1, Math.max(0, x)), Math.min(altura - 1, Math.max(0, y)))
  return png(largura, altura, (x, y) => {
    const dx = (h(x + 1, y) - h(x - 1, y)) * forca
    const dy = (h(x, y + 1) - h(x, y - 1)) * forca
    const n = Math.hypot(dx, dy, 1)
    return [((-dx / n) * 0.5 + 0.5) * 255, ((dy / n) * 0.5 + 0.5) * 255, ((1 / n) * 0.5 + 0.5) * 255, 255].map(Math.round)
  })
}
