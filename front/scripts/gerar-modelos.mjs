// Gera modelos em .glb com materiais PBR e texturas procedurais (cor, normal, emissiva).
// Uso: npm run modelos   ->  public/models/{carro,predio,torre,comercio,casa,medio}.glb
// Para trocar por texturas fotográficas: substitua os PNG embutidos (gltf-transform) ou refine no Blender.
import { Document, NodeIO } from '@gltf-transform/core'
import { KHRMaterialsClearcoat } from '@gltf-transform/extensions'
import { mkdirSync } from 'node:fs'
import { mapaNormal, png, ruido, ruidoSuave } from './png.mjs'

const doc = new Document()
const buf = doc.createBuffer()
const clearcoat = doc.createExtension(KHRMaterialsClearcoat)

// ---------- geometria ----------
const novaGeo = () => ({ pos: [], nor: [], uv: [], idx: [] })
const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]]
const cruz = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
const norm = (v) => {
  const l = Math.hypot(...v) || 1
  return v.map((c) => c / l)
}

/** Face convexa de 4 pontos; a normal é orientada para fora de `centro` (corrige o enrolamento sozinho). */
function face(g, pts, uvs, centro) {
  let n = norm(cruz(sub(pts[1], pts[0]), sub(pts[2], pts[0])))
  if (dot(n, sub(pts[0], centro)) < 0) {
    pts = [...pts].reverse()
    uvs = [...uvs].reverse()
    n = n.map((c) => -c)
  }
  const base = g.pos.length / 3
  pts.forEach((p, i) => {
    g.pos.push(...p)
    g.nor.push(...n)
    g.uv.push(...uvs[i])
  })
  g.idx.push(base, base + 1, base + 2, base, base + 2, base + 3)
}

/** Caixa; `uvPorMetro` ladrilha a textura (ex.: 0.5 = uma repetição a cada 2 m). */
function caixa(g, [cx, cy, cz], [w, h, d], { uvPorMetro = 0.5 } = {}) {
  const x = w / 2, y = h / 2, z = d / 2
  const c = [cx, cy, cz]
  const P = (sx, sy, sz) => [cx + sx * x, cy + sy * y, cz + sz * z]
  const uv = (a, b) => [[0, 0], [a * uvPorMetro, 0], [a * uvPorMetro, b * uvPorMetro], [0, b * uvPorMetro]]
  face(g, [P(-1, -1, 1), P(1, -1, 1), P(1, 1, 1), P(-1, 1, 1)], uv(w, h), c)
  face(g, [P(1, -1, -1), P(-1, -1, -1), P(-1, 1, -1), P(1, 1, -1)], uv(w, h), c)
  face(g, [P(1, -1, 1), P(1, -1, -1), P(1, 1, -1), P(1, 1, 1)], uv(d, h), c)
  face(g, [P(-1, -1, -1), P(-1, -1, 1), P(-1, 1, 1), P(-1, 1, -1)], uv(d, h), c)
  face(g, [P(-1, 1, 1), P(1, 1, 1), P(1, 1, -1), P(-1, 1, -1)], uv(w, d), c)
  face(g, [P(-1, -1, -1), P(1, -1, -1), P(1, -1, 1), P(-1, -1, 1)], uv(w, d), c)
}

/** Prisma trapezoidal: perfil (x, y) extrudado em Z. Usado na cabine do carro. */
function prisma(g, perfil, [cx, cy, cz], largura) {
  const z = largura / 2
  const centro = [cx + perfil.reduce((s, p) => s + p[0], 0) / perfil.length, cy + perfil.reduce((s, p) => s + p[1], 0) / perfil.length, cz]
  const V = (i, s) => [cx + perfil[i][0], cy + perfil[i][1], cz + s * z]
  const uvQuad = [[0, 0], [1, 0], [1, 1], [0, 1]]
  for (const s of [-1, 1]) face(g, [V(0, s), V(1, s), V(2, s), V(3, s)], uvQuad, centro)
  for (let i = 0; i < perfil.length; i++) {
    const j = (i + 1) % perfil.length
    face(g, [V(i, -1), V(j, -1), V(j, 1), V(i, 1)], uvQuad, centro)
  }
}

/** Cilindro com eixo em Z (roda). */
function cilindro(g, [cx, cy, cz], raio, largura, lados = 20) {
  const z0 = cz - largura / 2, z1 = cz + largura / 2
  for (let i = 0; i < lados; i++) {
    const a0 = (i / lados) * Math.PI * 2, a1 = ((i + 1) / lados) * Math.PI * 2
    const c = (a, z) => [cx + Math.cos(a) * raio, cy + Math.sin(a) * raio, z]
    face(g, [c(a0, z0), c(a1, z0), c(a1, z1), c(a0, z1)], [[i / lados, 0], [(i + 1) / lados, 0], [(i + 1) / lados, 1], [i / lados, 1]], [cx, cy, cz])
    for (const [z, nz] of [[z1, 1], [z0, -1]]) {
      const base = g.pos.length / 3
      g.pos.push(cx, cy, z, ...c(a0, z), ...c(a1, z))
      for (let k = 0; k < 3; k++) g.nor.push(0, 0, nz)
      g.uv.push(0.5, 0.5, 0.5 + Math.cos(a0) / 2, 0.5 + Math.sin(a0) / 2, 0.5 + Math.cos(a1) / 2, 0.5 + Math.sin(a1) / 2)
      g.idx.push(...(nz > 0 ? [base, base + 1, base + 2] : [base, base + 2, base + 1]))
    }
  }
}


/**
 * Superfície loftada ao longo de X: cada seção {x, w, y0, y1} é um retângulo de cantos arredondados no plano (z, y).
 * Normais suaves (soma das normais das faces vizinhas); as pontas são fechadas com leque. Dá carroceria curva em vez de caixa.
 */
function loft(g, secoes, { raio = 0.28, lados = 5 } = {}) {
  const anel = ({ x, w, y0, y1 }) => {
    const rr = Math.min(raio, w / 2 - 1e-3, (y1 - y0) / 2 - 1e-3)
    const cantos = [[w / 2 - rr, y1 - rr, 0], [-(w / 2 - rr), y1 - rr, 90], [-(w / 2 - rr), y0 + rr, 180], [w / 2 - rr, y0 + rr, 270]]
    const pts = []
    for (const [cz, cy, a0] of cantos) for (let i = 0; i <= lados; i++) {
      const a = ((a0 + (90 * i) / lados) * Math.PI) / 180
      pts.push([x, cy + Math.sin(a) * rr, cz + Math.cos(a) * rr])
    }
    return pts
  }
  const aneis = secoes.map(anel)
  const n = aneis[0].length
  const base = g.pos.length / 3
  const nor = []
  aneis.forEach((a, si) => a.forEach((p, i) => {
    g.pos.push(...p)
    g.uv.push((si / (aneis.length - 1)) * 1.5, i / n)
    nor.push([0, 0, 0])
  }))
  const idx = []
  const centroX = (si) => [aneis[si][0][0], (secoes[si].y0 + secoes[si].y1) / 2, 0]
  for (let si = 0; si < aneis.length - 1; si++) for (let i = 0; i < n; i++) {
    const j = (i + 1) % n
    const a = si * n + i, b = si * n + j, c = (si + 1) * n + j, d = (si + 1) * n + i
    let tri = [[a, b, c], [a, c, d]]
    const P = (k) => g.pos.slice((base + k) * 3, (base + k) * 3 + 3)
    const nf = norm(cruz(sub(P(b), P(a)), sub(P(c), P(a))))
    const m = [(P(a)[0] + P(c)[0]) / 2, (P(a)[1] + P(c)[1]) / 2, (P(a)[2] + P(c)[2]) / 2]
    if (dot(nf, sub(m, centroX(si))) < 0) tri = tri.map((t) => [t[0], t[2], t[1]])
    for (const t of tri) {
      const f = norm(cruz(sub(P(t[1]), P(t[0])), sub(P(t[2]), P(t[0]))))
      for (const k of t) nor[k] = [nor[k][0] + f[0], nor[k][1] + f[1], nor[k][2] + f[2]]
      idx.push(...t.map((k) => base + k))
    }
  }
  nor.forEach((v) => g.nor.push(...norm(v)))
  g.idx.push(...idx)
  // tampas
  for (const [si, sx] of [[0, -1], [aneis.length - 1, 1]]) {
    const c0 = g.pos.length / 3
    const cy = (secoes[si].y0 + secoes[si].y1) / 2
    g.pos.push(secoes[si].x, cy, 0)
    g.nor.push(sx, 0, 0)
    g.uv.push(0.5, 0.5)
    aneis[si].forEach((p) => { g.pos.push(...p); g.nor.push(sx, 0, 0); g.uv.push(0.5, 0.5) })
    for (let i = 0; i < n; i++) g.idx.push(...(sx > 0 ? [c0, c0 + 1 + i, c0 + 1 + ((i + 1) % n)] : [c0, c0 + 1 + ((i + 1) % n), c0 + 1 + i]))
  }
}

// ---------- materiais ----------
const lin = (c) => ((c /= 255) <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4)
const rgba = (hex) => [(hex >> 16) & 255, (hex >> 8) & 255, hex & 255].map(lin).concat(1)
const tex = (nome, bytes) => doc.createTexture(nome).setImage(bytes).setMimeType('image/png')

function material(nome, hex, rugosidade, metal, opc = {}) {
  const m = doc.createMaterial(nome).setBaseColorFactor(rgba(hex)).setRoughnessFactor(rugosidade).setMetallicFactor(metal)
  if (opc.base) m.setBaseColorTexture(opc.base)
  if (opc.normal) m.setNormalTexture(opc.normal).setNormalScale(opc.normalEsc ?? 1)
  if (opc.emissiva) m.setEmissiveTexture(opc.emissiva).setEmissiveFactor([1, 1, 1])
  if (opc.emissivoHex !== undefined) m.setEmissiveFactor(rgba(opc.emissivoHex).slice(0, 3))
  if (opc.verniz) m.setExtension('KHR_materials_clearcoat', clearcoat.createClearcoat().setClearcoatFactor(1).setClearcoatRoughnessFactor(0.06))
  return m
}

function malha(nome, g, mat) {
  const acc = (tipo, arr, T) => doc.createAccessor().setType(tipo).setArray(new T(arr)).setBuffer(buf)
  const prim = doc
    .createPrimitive()
    .setAttribute('POSITION', acc('VEC3', g.pos, Float32Array))
    .setAttribute('NORMAL', acc('VEC3', g.nor, Float32Array))
    .setAttribute('TEXCOORD_0', acc('VEC2', g.uv, Float32Array))
    .setIndices(acc('SCALAR', g.idx, Uint16Array))
    .setMaterial(mat)
  return doc.createMesh(nome).addPrimitive(prim)
}

const no = (nome, g, mat) => doc.createNode(nome).setMesh(malha(nome, g, mat))

async function salvar(arquivo, raiz) {
  const cena = doc.createScene(arquivo).addChild(raiz)
  doc.getRoot().setDefaultScene(cena)
  await new NodeIO().registerExtensions([KHRMaterialsClearcoat]).write(`public/models/${arquivo}.glb`, doc)
  for (const s of doc.getRoot().listScenes()) s.dispose()
  for (const n of doc.getRoot().listNodes()) n.dispose()
  for (const m of doc.getRoot().listMeshes()) m.dispose()
  // materiais, texturas e acessores também: sem isso o próximo arquivo levaria as sobras do anterior
  for (const m of doc.getRoot().listMaterials()) m.dispose()
  for (const t of doc.getRoot().listTextures()) t.dispose()
  for (const a of doc.getRoot().listAccessors()) a.dispose()
}

const q = (v, passos = 24) => Math.round(v * passos) / passos // quantiza: PNG comprime melhor

mkdirSync('public/models', { recursive: true })

// =====================================================================================
// CARRO
// =====================================================================================
{
  // Casca de laranja da pintura (normal) e variação sutil da cor base.
  const texPintura = tex('pintura', png(64, 64, (x, y) => {
    const g = 242 + ruido(x, y, 2) * 13
    return [g, g, g, 255].map(Math.round)
  }))
  const normPintura = tex('pintura_n', mapaNormal(128, 128, (x, y) => ruidoSuave(x / 2, y / 2, 4) * 0.7 + ruido(x, y, 9) * 0.3, 0.25))
  // Pneu: borracha fosca com granulado.
  const texPneu = tex('pneu', png(64, 64, (x, y) => {
    const g = 28 + ruido(x, y, 3) * 18
    return [g, g, g, 255].map(Math.round)
  }))

  const tinta = material('tinta', 0xffbe3c, 0.32, 0.3, { base: texPintura, normal: normPintura, normalEsc: 0.15, verniz: true })
  const vidro = material('vidro', 0x0f1722, 0.04, 0.1)
  const plastico = material('plastico', 0x14171c, 0.65, 0)
  const aro = material('aro', 0xc9d1da, 0.28, 1)
  const pneu = material('pneu', 0x1a1c20, 0.92, 0, { base: texPneu })
  const farol = material('farol', 0xf4f7ff, 0.2, 0, { emissivoHex: 0xdfe8ff })
  const lanterna = material('lanterna', 0xb3141a, 0.3, 0, { emissivoHex: 0xff2a2a })

  const gTinta = novaGeo(), gVidro = novaGeo(), gPlast = novaGeo(), gAro = novaGeo(), gPneu = novaGeo(), gFarol = novaGeo(), gLant = novaGeo()
  // Carroceria: seções ao longo do carro (largura, base, topo). Capô e porta-malas caem para as pontas.
  loft(gTinta, [
    { x: -2.2, w: 1.5, y0: 0.34, y1: 0.7 },
    { x: -1.95, w: 1.72, y0: 0.3, y1: 0.86 },
    { x: -1.2, w: 1.8, y0: 0.28, y1: 0.9 },
    { x: 0.2, w: 1.8, y0: 0.28, y1: 0.9 },
    { x: 1.2, w: 1.8, y0: 0.28, y1: 0.86 },
    { x: 1.95, w: 1.7, y0: 0.3, y1: 0.7 },
    { x: 2.2, w: 1.5, y0: 0.34, y1: 0.56 },
  ], { raio: 0.3 })
  // Cabine: afunila para o teto (colunas inclinadas) e vira vidro; o teto é um painel de pintura por cima.
  loft(gVidro, [
    { x: -1.3, w: 1.62, y0: 0.84, y1: 0.98 },
    { x: -0.85, w: 1.5, y0: 0.84, y1: 1.4 },
    { x: 0.1, w: 1.5, y0: 0.84, y1: 1.42 },
    { x: 0.7, w: 1.56, y0: 0.84, y1: 1.02 },
  ], { raio: 0.2 })
  loft(gTinta, [
    { x: -0.95, w: 1.44, y0: 1.38, y1: 1.46 },
    { x: -0.35, w: 1.5, y0: 1.38, y1: 1.47 },
    { x: 0.15, w: 1.44, y0: 1.38, y1: 1.46 },
  ], { raio: 0.04, lados: 2 })
  for (const s of [-1, 1]) caixa(gTinta, [0.55, 0.98, s * 1.0], [0.14, 0.1, 0.2]) // retrovisores
  caixa(gPlast, [2.16, 0.36, 0], [0.14, 0.2, 1.5]) // para-choque dianteiro
  caixa(gPlast, [-2.16, 0.36, 0], [0.14, 0.2, 1.46]) // para-choque traseiro
  caixa(gPlast, [2.19, 0.56, 0], [0.05, 0.14, 0.7]) // grade
  for (const s of [-1, 1]) caixa(gFarol, [2.14, 0.6, s * 0.56], [0.12, 0.1, 0.34]) // faróis
  for (const s of [-1, 1]) caixa(gLant, [-2.16, 0.68, s * 0.58], [0.1, 0.1, 0.38]) // lanternas
  for (const x of [1.4, -1.4]) for (const z of [0.9, -0.9]) {
    cilindro(gPneu, [x, 0.4, z], 0.4, 0.3)
    cilindro(gAro, [x, 0.4, z * 1.03], 0.27, 0.32)
  }

  const raiz = doc.createNode('carro')
  for (const [n, g, m] of [['carroceria', gTinta, tinta], ['vidro', gVidro, vidro], ['plasticos', gPlast, plastico], ['aros', gAro, aro], ['pneus', gPneu, pneu], ['farois', gFarol, farol], ['lanternas', gLant, lanterna]]) raiz.addChild(no(n, g, m))
  await salvar('carro', raiz)
}

// =====================================================================================
// PRÉDIO: fachada com baias, janelas com esquadria e vidro refletivo, térreo comercial,
// janelas acesas (emissiva) e juntas em relevo (normal).
// =====================================================================================
function fachada(baias, andares, semente) {
  const T = 64, L = baias * T, A = andares * T
  const base = new Uint8Array(L * A * 3), alt = new Float32Array(L * A), emi = new Uint8Array(L * A * 3)
  for (let y = 0; y < A; y++) for (let x = 0; x < L; x++) {
    const bx = Math.floor(x / T), by = Math.floor(y / T), u = x % T, v = y % T
    const terreo = by === andares - 1
    const i = y * L + x
    // concreto com manchas e escorrimentos
    const g = 168 + ruidoSuave(x / 6, y / 6, semente) * 34 + ruido(x, y, semente + 1) * 12 + ruidoSuave(x / 2, y / 40, semente + 2) * 18 * (v / T)
    let c = [g, g * 0.985, g * 0.96]
    let h = 0.5
    let e = [0, 0, 0]
    const acesa = ruido(bx, by, semente + 7) < (terreo ? 0.75 : 0.34)
    const vidroX = terreo ? u >= 4 && u <= 59 && v >= 16 && v <= 60 : u >= 10 && u <= 53 && v >= 10 && v <= 49
    const moldura = terreo ? u >= 2 && u <= 61 && v >= 14 && v <= 62 : u >= 7 && u <= 56 && v >= 7 && v <= 53
    if (v >= 58 && !terreo) { c = c.map((k) => k * 0.72); h = 0.62 } // laje
    if (terreo && v < 14) { c = [58, 64, 74]; h = 0.58 } // marquise
    if (moldura) { c = [46, 50, 56]; h = 0.64 }
    if (vidroX) {
      const refl = 1 - v / T
      const faixa = Math.abs(((u + v * 1.4) % 34) - 17) < 3 ? 26 : 0 // reflexo diagonal
      c = [48 + refl * 46 + faixa, 66 + refl * 58 + faixa, 88 + refl * 70 + faixa]
      h = 0.2
      if (!terreo && Math.abs(u - 31) < 1.2) { c = [42, 46, 52]; h = 0.6 } // montante central
      if (acesa) {
        c = [c[0] * 0.5 + 70, c[1] * 0.5 + 56, c[2] * 0.5 + 30]
        const brilho = 0.7 + ruido(bx, by, semente + 3) * 0.3
        e = [255 * brilho, 196 * brilho, 120 * brilho]
      }
    }
    if (terreo && vidroX && bx === 1 && u >= 24 && u <= 40) { c = [30, 34, 40]; h = 0.35 } // porta
    base[i * 3] = c[0]; base[i * 3 + 1] = c[1]; base[i * 3 + 2] = c[2]
    alt[i] = h
    emi[i * 3] = e[0]; emi[i * 3 + 1] = e[1]; emi[i * 3 + 2] = e[2]
  }
  const pix = (arr) => (x, y) => {
    const i = (y * L + x) * 3
    return [q(arr[i] / 255, 40) * 255, q(arr[i + 1] / 255, 40) * 255, q(arr[i + 2] / 255, 40) * 255, 255]
  }
  return {
    base: tex(`fachada_${semente}`, png(L, A, pix(base))),
    normal: tex(`fachada_n_${semente}`, mapaNormal(L, A, (x, y) => alt[y * L + x], 5)),
    emissiva: tex(`fachada_e_${semente}`, png(L, A, pix(emi))),
  }
}

async function construirPredio(arquivo, { baias, andares, prof, semente, tom = 0xffffff, telhado = 0xffffff }) {
  const frente = fachada(baias, andares, semente)
  const lado = fachada(prof, andares, semente + 8)
  const concretoH = (x, y) => ruidoSuave(x / 5, y / 5, 21) * 0.6 + ruido(x, y, 22) * 0.4
  const texTelhado = tex('telhado', png(128, 128, (x, y) => {
    const g = q((120 + concretoH(x, y) * 60) / 255, 40) * 255
    return [g, g, g * 0.98, 255].map(Math.round)
  }))
  const normTelhado = tex('telhado_n', mapaNormal(128, 128, concretoH, 1.5))

  // `tom` e `telhado` multiplicam a textura: o mesmo desenho de fachada vira concreto, reboco ou vidro frio.
  const mFrente = material('fachada_frente', tom, 0.55, 0, { base: frente.base, normal: frente.normal, emissiva: frente.emissiva })
  const mLado = material('fachada_lado', tom, 0.55, 0, { base: lado.base, normal: lado.normal, emissiva: lado.emissiva })
  const mTelhado = material('telhado', telhado, 0.9, 0, { base: texTelhado, normal: normTelhado })
  const mMetal = material('metal', 0x8a939e, 0.4, 0.85)

  const W = baias * 1.2, H = andares * 1.2, D = prof * 1.2 // cada baia e cada andar têm 1,2 m (escala estilizada)
  const centro = [0, H / 2, 0]
  const gFrente = novaGeo(), gLado = novaGeo(), gTop = novaGeo(), gMetal = novaGeo()
  const uvF = [[0, 1], [1, 1], [1, 0], [0, 0]]
  const x = W / 2, y = H / 2, z = D / 2
  const P = (sx, sy, sz) => [sx * x, H / 2 + sy * y, sz * z]
  face(gFrente, [P(-1, -1, 1), P(1, -1, 1), P(1, 1, 1), P(-1, 1, 1)], uvF, centro)
  face(gFrente, [P(1, -1, -1), P(-1, -1, -1), P(-1, 1, -1), P(1, 1, -1)], uvF, centro)
  face(gLado, [P(1, -1, 1), P(1, -1, -1), P(1, 1, -1), P(1, 1, 1)], uvF, centro)
  face(gLado, [P(-1, -1, -1), P(-1, -1, 1), P(-1, 1, 1), P(-1, 1, -1)], uvF, centro)
  caixa(gTop, [0, H + 0.12, 0], [W + 0.2, 0.24, D + 0.2], { uvPorMetro: 0.5 }) // laje de cobertura
  caixa(gTop, [-0.29 * W, H + 0.6, 0.17 * D], [0.25 * W, 0.72, 0.28 * D], { uvPorMetro: 0.5 }) // casa de máquinas
  caixa(gMetal, [0.25 * W, H + 0.5, -0.2 * D], [0.19 * W, 0.5, 0.2 * D]) // condensador
  caixa(gMetal, [0.04 * W, H + 0.42, 0.25 * D], [0.1 * W, 0.34, 0.14 * D]) // exaustor

  const raiz = doc.createNode(arquivo)
  raiz.addChild(no('frente', gFrente, mFrente)).addChild(no('lados', gLado, mLado)).addChild(no('cobertura', gTop, mTelhado)).addChild(no('equipamentos', gMetal, mMetal))
  await salvar(arquivo, raiz)
}

// Cinco tipos para a cena da viagem: o bairro não é feito de um prédio só.
await construirPredio('predio', { baias: 4, andares: 8, prof: 3, semente: 3 })
await construirPredio('torre', { baias: 5, andares: 13, prof: 4, semente: 5, tom: 0xc9d6e8 })
await construirPredio('comercio', { baias: 5, andares: 3, prof: 4, semente: 7, tom: 0xf0e2c8 })
await construirPredio('casa', { baias: 3, andares: 2, prof: 3, semente: 9, tom: 0xe8c9a6, telhado: 0xb0603a })
await construirPredio('medio', { baias: 4, andares: 5, prof: 3, semente: 13, tom: 0xbac4b2 })

console.log('modelos gerados em public/models')
