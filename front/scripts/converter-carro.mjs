// Converte o carro de fontes-3d/meshfleet (Sketchfab, CC-BY, via MeshFleet) para o padrão da cena:
// frente em +X, 4,4 unidades de comprimento, centrado em X/Z e apoiado em y = 0.
// Uso: node scripts/converter-carro.mjs <entrada.glb> [saida.glb] [anguloGraus]
import { NodeIO } from '@gltf-transform/core'
import { getBounds } from '@gltf-transform/functions'

const [entrada, saida = 'public/models/carro-corolla.glb', angulo = '90'] = process.argv.slice(2)
const COMPRIMENTO = 4.4
const doc = await new NodeIO().read(entrada)
const cena = doc.getRoot().listScenes()[0]
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
