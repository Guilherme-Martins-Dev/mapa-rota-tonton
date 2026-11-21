// Converte o carro de fontes-3d/meshfleet (Sketchfab, CC-BY, via MeshFleet) para o padrão da cena:
// frente em +X, 4,4 unidades de comprimento, centrado em X/Z e apoiado em y = 0.
// Uso: node scripts/converter-carro.mjs <entrada.glb> [saida.glb] [anguloGraus]
import { NodeIO } from '@gltf-transform/core'
import { getBounds } from '@gltf-transform/functions'

const [entrada, saida = 'public/models/carro-corolla.glb', angulo = '90'] = process.argv.slice(2)
const COMPRIMENTO = 4.4
const doc = await new NodeIO().read(entrada)
const cena = doc.getRoot().listScenes()[0]
// ---- separa as 4 rodas (vêm fundidas numa malha só) em nós próprios: direcao_* (esterça, eixo Y) > roda_* (rola, eixo X) ----
function separarRodas() {
  const no = doc.getRoot().listNodes().find((n) => n.getMesh()?.getName().startsWith('wheel'))
  if (!no) return
  const malha = no.getMesh()
  const prim = malha.listPrimitives()[0]
  const pos = prim.getAttribute('POSITION'), nor = prim.getAttribute('NORMAL'), uv = prim.getAttribute('TEXCOORD_0')
  const ind = prim.getIndices().getArray()
  const n = pos.getCount()
  const P = Array.from({ length: n }, (_, i) => pos.getElement(i, [0, 0, 0]))
  // posição do vértice no espaço do modelo = translação dos nós acima (sem rotação neste arquivo)
  const mundo = [0, 0, 0]
  for (let a = no; a && a.getParentNode(); a = a.getParentNode()) a.getTranslation().forEach((x, i) => (mundo[i] += x))
  const medio = [0, 1, 2].map((i) => (Math.min(...P.map((p) => p[i])) + Math.max(...P.map((p) => p[i]))) / 2)
  const grupo = P.map((p) => (p[0] + mundo[0] > 0 ? 1 : 0) + (p[2] + mundo[2] > medio[2] + mundo[2] ? 2 : 0))
  const buf = doc.getRoot().listBuffers()[0]
  const acc = (tipo, arr) => doc.createAccessor().setType(tipo).setArray(arr).setBuffer(buf)
  const nomes = ['tras_a', 'tras_b', 'frente_a', 'frente_b']
  for (let g = 0; g < 4; g++) {
    const ids = P.map((_, i) => i).filter((i) => grupo[i] === g)
    // centro do eixo = centro da caixa da roda (não a média dos vértices: o cubo e a banda de rodagem deslocariam o pivô e a roda balançaria)
    const c = [0, 1, 2].map((a) => (Math.min(...ids.map((i) => P[i][a])) + Math.max(...ids.map((i) => P[i][a]))) / 2)
    const novo = new Map(ids.map((id, k) => [id, k]))
    const tris = []
    for (let t = 0; t < ind.length; t += 3) if (novo.has(ind[t]) && novo.has(ind[t + 1]) && novo.has(ind[t + 2])) tris.push(novo.get(ind[t]), novo.get(ind[t + 1]), novo.get(ind[t + 2]))
    const f = (fonte, dim, centro) => { const out = new Float32Array(ids.length * dim); ids.forEach((id, k) => { const e = fonte.getElement(id, new Array(dim).fill(0)); for (let d = 0; d < dim; d++) out[k * dim + d] = e[d] - (centro ? centro[d] : 0) }); return out }
    const p2 = doc.createPrimitive().setAttribute('POSITION', acc('VEC3', f(pos, 3, c))).setAttribute('NORMAL', acc('VEC3', f(nor, 3))).setAttribute('TEXCOORD_0', acc('VEC2', f(uv, 2))).setIndices(acc('SCALAR', new Uint16Array(tris))).setMaterial(prim.getMaterial())
    const roda = doc.createNode('roda_' + nomes[g]).setMesh(doc.createMesh('roda_' + nomes[g]).addPrimitive(p2))
    const dir = doc.createNode('direcao_' + nomes[g]).setTranslation([no.getTranslation()[0] + c[0] + 0, no.getTranslation()[1] + c[1], no.getTranslation()[2] + c[2]]).addChild(roda)
    no.getParentNode().addChild(dir)
  }
  no.getMesh().dispose()
  no.setMesh(null)
  console.log('rodas separadas; raio ~', (Math.max(...P.map((p) => p[1])) - Math.min(...P.map((p) => p[1]))) / 2)
}
separarRodas()

const { min, max } = getBounds(cena)
const dim = [0, 1, 2].map((i) => max[i] - min[i])
const eixoLongo = dim[0] > dim[2] ? 0 : 2
const s = COMPRIMENTO / dim[eixoLongo]
const th = (Number(angulo) * Math.PI) / 180
const c = [(min[0] + max[0]) / 2, (min[2] + max[2]) / 2]
const v = [s * c[0], s * c[1]]
const giro = [v[0] * Math.cos(th) + v[1] * Math.sin(th), -v[0] * Math.sin(th) + v[1] * Math.cos(th)]
const pai = doc.createNode('carro')
  .setRotation([0, Math.sin(th / 2), 0, Math.cos(th / 2)])
  .setScale([s, s, s])
  .setTranslation([-giro[0], -s * min[1], -giro[1]])
for (const filho of cena.listChildren()) {
  cena.removeChild(filho)
  pai.addChild(filho)
}
cena.addChild(pai)
await new NodeIO().write(saida, doc)
const b = getBounds(cena)
console.log('eixo longo', 'xyz'[eixoLongo], 'escala', s.toFixed(4), 'bbox', b.min.map((n) => +n.toFixed(2)), b.max.map((n) => +n.toFixed(2)))
