/**
 * Troca de tema com um carro: ele atravessa a tela derrapando e as marcas dos pneus traseiros se espalham como tinta,
 * revelando o tema novo (View Transitions + clip-path). A cor do carro e das marcas é a do tema que chega (token `--carro`).
 * Sem movimento (preferência do sistema) a troca é imediata; sem View Transitions, as cores mudam em fade.
 */
export type Tema = 'light' | 'dark'
export const EVENTO_TEMA = 'tema:alterado'

const T_CARRO = 1500 // ms de percurso do carro
const T_ESPALHA = 900 // ms que cada marca leva para se espalhar
const T_TOTAL = T_CARRO + T_ESPALHA

const limita = (x: number, a = 0, b = 1) => Math.min(b, Math.max(a, x))
const saida = (x: number) => 1 - (1 - limita(x)) ** 3

/** Trajetória: entra embaixo à esquerda, sobe em S e sai em cima à direita (u de 0 a 1). */
function pista(u: number, W: number, H: number) {
  return { x: -0.08 * W + u * 1.16 * W, y: H * (0.66 - 0.38 * u + 0.15 * Math.sin(u * Math.PI * 2.4)) }
}

function desenhaCarro(c: CanvasRenderingContext2D, x: number, y: number, ang: number, L: number, cor: string) {
  const A = L * 0.5
  c.save()
  c.translate(x, y)
  c.rotate(ang)
  c.fillStyle = 'rgba(0,0,0,0.28)'
  c.beginPath()
  c.roundRect(-L / 2 + 3, -A / 2 + 5, L, A, A * 0.3)
  c.fill()
  c.fillStyle = 'rgba(0,0,0,0.85)' // rodas
  for (const [wx, wy] of [[0.3, -0.5], [0.3, 0.5], [-0.3, -0.5], [-0.3, 0.5]]) {
    c.beginPath()
    c.roundRect(wx * L - L * 0.1, wy * A - A * 0.1, L * 0.2, A * 0.2, 3)
    c.fill()
  }
  c.fillStyle = cor
  c.beginPath()
  c.roundRect(-L / 2, -A / 2, L, A, A * 0.3)
  c.fill()
  c.fillStyle = 'rgba(10,14,20,0.8)' // cabine e vidros
  c.beginPath()
  c.roundRect(-L * 0.2, -A * 0.38, L * 0.36, A * 0.76, A * 0.14)
  c.fill()
  c.fillStyle = 'rgba(255,246,200,0.95)' // faróis
  c.fillRect(L * 0.44, -A * 0.4, L * 0.05, A * 0.2)
  c.fillRect(L * 0.44, A * 0.2, L * 0.05, A * 0.2)
  c.fillStyle = 'rgba(255,60,60,0.95)' // lanternas
  c.fillRect(-L * 0.5, -A * 0.4, L * 0.04, A * 0.2)
  c.fillRect(-L * 0.5, A * 0.2, L * 0.04, A * 0.2)
  c.restore()
}

let ocupado = false

/** Roda a transição; `aplicar` troca o tema de fato (chamado uma vez, com a tela antiga já capturada). */
export async function trocarTemaComCarro(aplicar: () => void): Promise<void> {
  const html = document.documentElement
  if (ocupado) return
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return aplicar()
  if (!document.startViewTransition) {
    html.classList.add('tema-fade')
    aplicar()
    window.setTimeout(() => html.classList.remove('tema-fade'), 500)
    return
  }
  ocupado = true
  const W = window.innerWidth
  const H = window.innerHeight
  const dpr = Math.min(2, window.devicePixelRatio || 1)
  const tela = document.createElement('canvas')
  tela.width = Math.round(W * dpr)
  tela.height = Math.round(H * dpr)
  tela.setAttribute('aria-hidden', 'true')
  tela.className = 'carro-tema'
  const estilo = document.createElement('style')
  estilo.textContent = 'html.carro-ativa::view-transition-new(root){clip-path:circle(0px at 0 0)}'
  document.head.append(estilo)
  document.body.append(tela) // no <head> o canvas ficaria com display:none e o carro nunca apareceria
  html.classList.add('carro-ativa')
  try {
    const vt = document.startViewTransition(aplicar)
    await vt.ready
    const ctx = tela.getContext('2d')!
    ctx.scale(dpr, dpr)
    const cor = getComputedStyle(html).getPropertyValue('--carro').trim() || '#4cc9f0'
    const L = Math.max(64, Math.min(120, W * 0.085))
    const diag = Math.hypot(W, H)
    const marcas: { x: number; y: number; t: number }[][] = [[], []]
    let corpoAnt = 0
    // Mantém a transição viva pelo tempo todo; o recorte é reescrito a cada quadro.
    html.animate([{ opacity: 1 }, { opacity: 1 }], { duration: T_TOTAL + 120, pseudoElement: '::view-transition-new(root)' })
    const t0 = performance.now()
    await new Promise<void>((fim) => {
      const quadro = (agora: number) => {
        const t = agora - t0
        ctx.clearRect(0, 0, W, H)
        const u = limita(t / T_CARRO)
        const d = 0.012
        const p = pista(u, W, H)
        const a = pista(Math.max(0, u - d), W, H)
        const b = pista(Math.min(1, u + d), W, H)
        const rumo = Math.atan2(b.y - a.y, b.x - a.x)
        const giro0 = Math.atan2(p.y - a.y, p.x - a.x)
        const giro1 = Math.atan2(b.y - p.y, b.x - p.x)
        const giro = Math.atan2(Math.sin(giro1 - giro0), Math.cos(giro1 - giro0))
        // Derrapagem: o corpo gira além do rumo, para dentro da curva, e volta suavemente.
        corpoAnt += (limita(giro * 22, -0.9, 0.9) - corpoAnt) * 0.18
        const ang = rumo + corpoAnt
        if (u < 1) {
          const tras = L * 0.3
          const lado = L * 0.2
          ;[-1, 1].forEach((s, i) => {
            marcas[i].push({
              x: p.x - Math.cos(ang) * tras - Math.sin(ang) * lado * s,
              y: p.y - Math.sin(ang) * tras + Math.cos(ang) * lado * s,
              t,
            })
          })
        }
        // marcas de pneu
        ctx.lineCap = 'round'
        ctx.lineJoin = 'round'
        ctx.strokeStyle = cor
        ctx.globalAlpha = 0.9 * (1 - saida((t - (T_TOTAL - 450)) / 450))
        ctx.lineWidth = Math.max(4, L * 0.07)
        for (const m of marcas) {
          ctx.beginPath()
          m.forEach((q, k) => (k ? ctx.lineTo(q.x, q.y) : ctx.moveTo(q.x, q.y)))
          ctx.stroke()
        }
        ctx.globalAlpha = 1
        if (u < 1) desenhaCarro(ctx, p.x, p.y, ang, L, cor)
        // recorte: círculos nas marcas, que crescem como tinta; no fim, a tela inteira
        const final = t >= T_TOTAL
        const base = 0.22 * diag + diag * 0.9 * saida((t - T_CARRO * 0.6) / (T_TOTAL - T_CARRO * 0.6))
        let caminho = ''
        if (!final) {
          for (const m of marcas) {
            for (let k = 0; k < m.length; k += 2) {
              const r = base * saida((t - m[k].t) / T_ESPALHA)
              if (r < 1) continue
              caminho += `M${(m[k].x - r).toFixed(1)} ${m[k].y.toFixed(1)}a${r.toFixed(1)} ${r.toFixed(1)} 0 1 0 ${(2 * r).toFixed(1)} 0a${r.toFixed(1)} ${r.toFixed(1)} 0 1 0 ${(-2 * r).toFixed(1)} 0Z`
            }
          }
        }
        const recorte = final ? 'inset(0)' : caminho ? `path("${caminho}")` : 'circle(0px at 0 0)'
        estilo.textContent = `html.carro-ativa::view-transition-new(root){clip-path:${recorte}}`
        if (final) fim()
        else requestAnimationFrame(quadro)
      }
      requestAnimationFrame(quadro)
    })
    await vt.finished
  } catch {
    /* transição interrompida (aba em segundo plano, etc.): o tema já foi aplicado */
  } finally {
    html.classList.remove('carro-ativa')
    tela.remove()
    estilo.remove()
    ocupado = false
  }
}
