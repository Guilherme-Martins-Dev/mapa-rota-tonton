// Codificador PNG mínimo (RGBA, sem dependências) para texturas procedurais.
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
  return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), bloco('IHDR', ihdr), bloco('IDAT', deflateSync(raw)), bloco('IEND', Buffer.alloc(0))])
}

/** Ruído de valor determinístico, para variação sutil de superfície. */
export function ruido(x, y, semente = 1) {
  const s = Math.sin(x * 127.1 + y * 311.7 + semente * 74.7) * 43758.5453
  return s - Math.floor(s)
}
