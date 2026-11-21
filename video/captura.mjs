// Grava cada cena do vídeo comercial em captura/<cena>.webm + .json (marcas de tempo).
// Uso: node captura.mjs [cena ...]    Requer: front rodando em :5173 e audio/cenas/<cena>.json (duração da narração).
import { chromium } from 'playwright'
import { readFileSync, writeFileSync, mkdirSync, renameSync, existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const AQUI = path.dirname(fileURLToPath(import.meta.url))
const BASE = 'http://localhost:5173'
const W = 1920, H = 1080
const quais = process.argv.slice(2)

/** Rolagem animada dentro da página (rAF, tempo real): keyframes [{t: 0..1, y}] com suavização. */
const ROLAR = `(({ pontos, ms }) => new Promise((ok) => {
  const t0 = performance.now(), ease = (x) => x * x * (3 - 2 * x)
  const passo = () => {
    const k = Math.min(1, (performance.now() - t0) / ms)
    let i = 0; while (i < pontos.length - 2 && k > pontos[i + 1].t) i++
    const a = pontos[i], b = pontos[i + 1], q = Math.min(1, Math.max(0, (k - a.t) / (b.t - a.t)))
    window.scrollTo(0, a.y + (b.y - a.y) * ease(q))
    k < 1 ? requestAnimationFrame(passo) : ok()
  }
  passo()
}))`

/** Posição de rolagem (px) do progresso p da viagem (seção pinada de 1700% da tela). */
const yViagem = `(p) => window.__top + p * 17 * innerHeight`

const CENAS = {
  c1_gancho: async (p, ms) => {
    await p.evaluate(`${ROLAR}({ pontos: [{ t: 0, y: 0 }, { t: 1, y: innerHeight * 0.45 }], ms: ${ms} })`)
  },
  c2_apresenta: async (p, ms) => {
    await p.evaluate(`window.__alvo = (${yViagem})(0.17)`)
    await p.evaluate(`window.scrollTo(0, innerHeight * 0.45)`); await p.waitForTimeout(1200)
    marcas.inicio = Date.now() - marcas.t0
    await p.evaluate(`${ROLAR}({ pontos: [{ t: 0, y: innerHeight * 0.45 }, { t: 1, y: window.__alvo }], ms: ${ms} })`)
  },
  c3_grafo: async (p, ms) => viagem(p, ms, 0.17, 0.38),
  c4_pesos: async (p, ms) => viagem(p, ms, 0.39, 0.585),
  c5_consumo: async (p, ms) => viagem(p, ms, 0.59, 0.79),
  c6_mapa: async (p, ms) => {
    await p.goto(`${BASE}/mapa`, { waitUntil: 'load' }); await p.waitForTimeout(7000)
    const t0 = Date.now(); marcas.inicio = t0 - marcas.t0
    const passos = ['Menor distância', 'Menor tempo', 'Menor consumo']
    for (let i = 0; i < passos.length; i++) {
      await p.locator(`label[data-criterio="${['distancia', 'tempo', 'consumo'][i]}"]`).click({ timeout: 4000 }).catch(() => {})
      await p.waitForTimeout(Math.max(0, (ms * (i + 1)) / passos.length - (Date.now() - t0)))
    }
  },
  c7_construcao: async (p, ms) => {
    await p.goto(`${BASE}/construcao`, { waitUntil: 'load' }); await p.waitForTimeout(3500)
    marcas.inicio = Date.now() - marcas.t0
    const alvo = await p.evaluate(`(document.querySelector('#perguntas')?.getBoundingClientRect().top ?? 4000) + scrollY - 40`)
    await p.evaluate(`${ROLAR}({ pontos: [{ t: 0, y: 0 }, { t: 1, y: ${alvo} }], ms: ${ms} })`)
  },
  c8_fecho: async (p, ms) => {
    await p.goto(`file:///${AQUI.split(path.sep).join('/')}/fecho.html`, { waitUntil: 'load' }); await p.waitForTimeout(500)
    marcas.inicio = Date.now() - marcas.t0
    await p.waitForTimeout(ms)
  },
}
let marcas = {}

async function viagem(p, ms, de, ate) {
  await p.evaluate(`window.scrollTo(0, (${yViagem})(${de}))`); await p.waitForTimeout(3500)
  marcas.inicio = Date.now() - marcas.t0
  await p.evaluate(`${ROLAR}({ pontos: [{ t: 0, y: (${yViagem})(${de}) }, { t: 1, y: (${yViagem})(${ate}) }], ms: ${ms} })`)
}

mkdirSync(path.join(AQUI, 'captura'), { recursive: true })
const b = await chromium.launch({ channel: 'msedge', headless: true, args: ['--use-angle=d3d11', '--enable-gpu-rasterization', '--ignore-gpu-blocklist', '--enable-zero-copy'] })
for (const [id, fn] of Object.entries(CENAS)) {
  if (quais.length && !quais.includes(id)) continue
  const dur = JSON.parse(readFileSync(path.join(AQUI, 'audio', 'cenas', `${id}.json`), 'utf8')).duracao
  const ms = Math.round((dur + 0.8) * 1000)
  const tmp = path.join(AQUI, 'captura', `_${id}`)
  const c = await b.newContext({ viewport: { width: W, height: H }, recordVideo: { dir: tmp, size: { width: W, height: H } } })
  const p = await c.newPage()
  marcas = { t0: Date.now() }
  // cenas de home: abrir a home e esperar a cena 3D assentar
  if (!['c6_mapa', 'c7_construcao', 'c8_fecho'].includes(id)) {
    await p.goto(`${BASE}/`, { waitUntil: 'load' }); await p.waitForTimeout(6000)
    await p.evaluate(`window.__top = document.querySelector('#viagem').getBoundingClientRect().top + scrollY`) // base medida com a página no topo, antes do pin
    if (id === 'c1_gancho') marcas.inicio = Date.now() - marcas.t0
  }
  await fn(p, ms)
  marcas.fim = Date.now() - marcas.t0
  const video = p.video()
  await c.close()
  const arq = await video.path()
  renameSync(arq, path.join(AQUI, 'captura', `${id}.webm`))
  writeFileSync(path.join(AQUI, 'captura', `${id}.json`), JSON.stringify({ ...marcas, ms }))
  console.log('capturado', id, marcas)
}
await b.close()
