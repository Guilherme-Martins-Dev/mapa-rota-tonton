// Gera modelos low-poly em .glb (PBR, com normais e UVs prontos para receber textura).
// Uso: node scripts/gerar-modelos.mjs   ->  public/models/*.glb
// Para texturizar depois: troque o material por baseColorTexture/normalTexture no .glb (gltf-transform) ou no Blender.
import { Document, NodeIO } from '@gltf-transform/core'
import { mkdirSync } from 'node:fs'
import { png, ruido } from './png.mjs'

const doc = new Document()
const buf = doc.createBuffer()

/** Geometria em listas planas; cada face tem seus próprios vértices (normais duras, UVs 0..1). */
function novaGeo() {
  return { pos: [], nor: [], uv: [], idx: [] }
}

function quad(g, p, n) {
  const base = g.pos.length / 3
  for (const v of p) g.pos.push(...v)
  for (let i = 0; i < 4; i++) g.nor.push(...n)
  g.uv.push(0, 0, 1, 0, 1, 1, 0, 1)
  g.idx.push(base, base + 1, base + 2, base, base + 2, base + 3)
}

function caixa(g, [cx, cy, cz], [w, h, d]) {
  const x = w / 2, y = h / 2, z = d / 2
  const P = (sx, sy, sz) => [cx + sx * x, cy + sy * y, cz + sz * z]
  quad(g, [P(-1, -1, 1), P(1, -1, 1), P(1, 1, 1), P(-1, 1, 1)], [0, 0, 1])
  quad(g, [P(1, -1, -1), P(-1, -1, -1), P(-1, 1, -1), P(1, 1, -1)], [0, 0, -1])
  quad(g, [P(1, -1, 1), P(1, -1, -1), P(1, 1, -1), P(1, 1, 1)], [1, 0, 0])
  quad(g, [P(-1, -1, -1), P(-1, -1, 1), P(-1, 1, 1), P(-1, 1, -1)], [-1, 0, 0])
  quad(g, [P(-1, 1, 1), P(1, 1, 1), P(1, 1, -1), P(-1, 1, -1)], [0, 1, 0])
  quad(g, [P(-1, -1, -1), P(1, -1, -1), P(1, -1, 1), P(-1, -1, 1)], [0, -1, 0])
}

/** Cilindro com eixo em Z (roda); `lados` baixo mantém o peso do arquivo mínimo. */
function cilindro(g, [cx, cy, cz], raio, largura, lados = 12) {
  const z0 = cz - largura / 2, z1 = cz + largura / 2
  for (let i = 0; i < lados; i++) {
    const a0 = (i / lados) * Math.PI * 2, a1 = ((i + 1) / lados) * Math.PI * 2
    const c = (a, z) => [cx + Math.cos(a) * raio, cy + Math.sin(a) * raio, z]
    const am = (a0 + a1) / 2
    quad(g, [c(a0, z0), c(a1, z0), c(a1, z1), c(a0, z1)], [Math.cos(am), Math.sin(am), 0])
    for (const [z, nz] of [[z1, 1], [z0, -1]]) {
      const base = g.pos.length / 3
      g.pos.push(cx, cy, z, ...c(a0, z), ...c(a1, z))
      for (let k = 0; k < 3; k++) g.nor.push(0, 0, nz)
      g.uv.push(0.5, 0.5, 0.5 + Math.cos(a0) / 2, 0.5 + Math.sin(a0) / 2, 0.5 + Math.cos(a1) / 2, 0.5 + Math.sin(a1) / 2)
      g.idx.push(...(nz > 0 ? [base, base + 1, base + 2] : [base, base + 2, base + 1]))
    }
  }
}

/** Textura PNG embutida no .glb como baseColorTexture (multiplica o fator de cor). */
function textura(nome, largura, altura, pixel) {
  return doc.createTexture(nome).setImage(png(largura, altura, pixel)).setMimeType('image/png')
}

function material(nome, cor, rugosidade, metal, tex) {
  // hex sRGB -> fator linear (glTF espera baseColorFactor linear)
  const lin = (c) => ((c /= 255) <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4)
  const rgba = [(cor >> 16) & 255, (cor >> 8) & 255, cor & 255].map(lin).concat(1)
  const m = doc.createMaterial(nome).setBaseColorFactor(rgba).setRoughnessFactor(rugosidade).setMetallicFactor(metal)
  if (tex) m.setBaseColorTexture(tex)
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

async function salvar(arquivo, raiz) {
  const cena = doc.createScene(arquivo).addChild(raiz)
  doc.getRoot().setDefaultScene(cena)
  await new NodeIO().write(`public/models/${arquivo}.glb`, doc)
  for (const s of doc.getRoot().listScenes()) s.dispose()
  for (const n of doc.getRoot().listNodes()) n.dispose()
  for (const m of doc.getRoot().listMeshes()) m.dispose()
}

mkdirSync('public/models', { recursive: true })

// Pintura: cinza claro com granulado e riscos finos (multiplica a cor âmbar da carroceria).
const texPintura = textura('pintura', 128, 128, (x, y) => {
  const g = 225 + ruido(x, y) * 30 - (y % 64 === 0 || x % 64 === 0 ? 40 : 0)
  return [g, g, g, 255]
})
// Concreto: manchas de ruído em duas escalas.
const texConcreto = textura('concreto', 128, 128, (x, y) => {
  const g = 170 + ruido(x >> 3, y >> 3, 3) * 50 + ruido(x, y, 5) * 25
  return [g, g, g, 255]
})
// Janela: moldura escura e reflexo em degradê vertical (o cinza escala a cor ciano do material).
const texJanela = textura('janela', 64, 64, (x, y) => {
  const borda = x < 4 || y < 4 || x > 59 || y > 59
  const g = borda ? 60 : 150 + (y / 64) * 100
  return [g, g, g, 255]
})

// ---- carro: carroceria, cabine/vidro, rodas ----
{
  const carroceria = novaGeo(), vidro = novaGeo(), pneu = novaGeo()
  caixa(carroceria, [0, 0.55, 0], [4.2, 0.7, 1.8])
  caixa(carroceria, [0.1, 0.95, 0], [3.2, 0.12, 1.7]) // capô/teto base
  caixa(vidro, [-0.2, 1.22, 0], [2.2, 0.55, 1.62])
  caixa(carroceria, [-0.2, 1.54, 0], [2.0, 0.1, 1.55]) // teto
  for (const [x, z] of [[1.35, 0.95], [1.35, -0.95], [-1.35, 0.95], [-1.35, -0.95]]) cilindro(pneu, [x, 0.38, z], 0.38, 0.3)
  const no = doc.createNode('carro')
    .addChild(doc.createNode('carroceria').setMesh(malha('carroceria', carroceria, material('tinta', 0xffbe3c, 0.35, 0.6, texPintura))))
    .addChild(doc.createNode('vidro').setMesh(malha('vidro', vidro, material('vidro', 0x1a2230, 0.1, 0.2))))
    .addChild(doc.createNode('rodas').setMesh(malha('rodas', pneu, material('pneu', 0x111418, 0.9, 0))))
  await salvar('carro', no)
}

// ---- prédio: bloco com janelas em relevo para fachada texturizável ----
{
  const parede = novaGeo(), janela = novaGeo()
  caixa(parede, [0, 3, 0], [3, 6, 3])
  for (let andar = 0; andar < 4; andar++)
    for (const x of [-0.8, 0.8]) {
      caixa(janela, [x, 1.2 + andar * 1.3, 1.52], [0.9, 0.7, 0.05])
      caixa(janela, [x, 1.2 + andar * 1.3, -1.52], [0.9, 0.7, 0.05])
    }
  const no = doc.createNode('predio')
    .addChild(doc.createNode('parede').setMesh(malha('parede', parede, material('concreto', 0x3a4558, 0.85, 0, texConcreto))))
    .addChild(doc.createNode('janelas').setMesh(malha('janelas', janela, material('janela', 0x4cc9f0, 0.2, 0.1, texJanela))))
  await salvar('predio', no)
}

console.log('modelos gerados em public/models')
