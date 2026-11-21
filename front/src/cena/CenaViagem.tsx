import { Clone, ContactShadows, Environment, Lightformer, useGLTF } from '@react-three/drei'
import { Canvas, useFrame } from '@react-three/fiber'
import { useMemo, useRef, useState } from 'react'
import { BufferGeometry, Float32BufferAttribute, MathUtils, type Group, type Object3D, type PointLight } from 'three'
import { corToken } from '../cores'
import type { RotaFeature } from '../data/tipos'
import { Caminho, criarCaminho, distribuirPredios, type Predio, type TipoPredio } from './caminho'
import { INTRO_VIAGEM, viagem } from './progresso'

const MEIA_PISTA = 2.2
const CALCADA = 3.6
const ALTURA_CAMERA = 2.3
const ATRAS_CAMERA = 5.4
const MAX_CAMERA = 16
const ALTURA_AEREA = 36

/** Faixa de largura variável ao longo de [s0, s1], entre os recuos o1 e o2 da linha central, no nível y. */
function fita(rua: Caminho, o1: number, o2: number, y: number, s0 = 0, s1 = rua.comprimento): BufferGeometry {
  const pos: number[] = []
  const idx: number[] = []
  const n = Math.max(1, Math.round((s1 - s0) / rua.passo))
  for (let i = 0; i <= n; i++) {
    const c = rua.em(s0 + ((s1 - s0) * i) / n)
    const nx = -c.tz, nz = c.tx
    pos.push(c.x + nx * o1, y, c.z + nz * o1, c.x + nx * o2, y, c.z + nz * o2)
    if (i > 0) {
      const a = (i - 1) * 2
      idx.push(a, a + 1, a + 2, a + 1, a + 3, a + 2)
    }
  }
  const g = new BufferGeometry()
  g.setAttribute('position', new Float32BufferAttribute(pos, 3))
  g.setAttribute('normal', new Float32BufferAttribute(new Array(pos.length).fill(0).map((_, i) => (i % 3 === 1 ? 1 : 0)), 3))
  g.setIndex(idx)
  return g
}

/** Pista, calçadas e faixa central tracejada, todas seguindo as curvas da rota. */
function Via({ rua }: { rua: Caminho }) {
  const geos = useMemo(() => {
    const tracos: BufferGeometry[] = []
    for (let s = 2; s < rua.comprimento - 4; s += 6) tracos.push(fita(rua, -0.07, 0.07, 0.014, s, s + 3))
    return {
      asfalto: fita(rua, -MEIA_PISTA, MEIA_PISTA, 0.004),
      calcadaE: fita(rua, -CALCADA, -MEIA_PISTA, 0.09),
      calcadaD: fita(rua, MEIA_PISTA, CALCADA, 0.09),
      tracos,
    }
  }, [rua])
  const cor = useMemo(
    () => ({ asfalto: corToken('superficie'), calcada: corToken('superficie-2'), faixa: corToken('c-tempo') }),
    [],
  )
  return (
    <group>
      <mesh geometry={geos.asfalto}><meshStandardMaterial color={cor.asfalto} roughness={0.9} /></mesh>
      <mesh geometry={geos.calcadaE}><meshStandardMaterial color={cor.calcada} roughness={0.95} /></mesh>
      <mesh geometry={geos.calcadaD}><meshStandardMaterial color={cor.calcada} roughness={0.95} /></mesh>
      {geos.tracos.map((g, i) => (
        <mesh key={i} geometry={g}><meshBasicMaterial color={cor.faixa} /></mesh>
      ))}
    </group>
  )
}

type Modelos = Record<TipoPredio, Object3D>

/** Só monta os prédios perto do carro (atrás e, principalmente, à frente até onde a neblina esconde). */
function Vizinhos({ predios, sRef, modelos }: { predios: Predio[]; sRef: { current: number }; modelos: Modelos }) {
  const [balde, setBalde] = useState(0)
  useFrame(() => {
    const b = Math.floor(sRef.current / 15)
    if (b !== balde) setBalde(b)
  })
  const visiveis = useMemo(() => predios.filter((p) => p.s > balde * 15 - 40 && p.s < balde * 15 + 130), [predios, balde])
  return (
    <>
      {visiveis.map((p) => (
        <Clone key={`${p.x}|${p.z}`} object={modelos[p.tipo]} position={[p.x, 0, p.z]} rotation={[0, p.rotY, 0]} scale={p.escala} />
      ))}
    </>
  )
}

const damp = MathUtils.damp

/** Carro e câmera de perseguição guiados por `viagem.valor` (0..1). O carro aponta para a tangente da rua. */
function Passeio({ rua, predios }: { rua: Caminho; predios: Predio[] }) {
  const carro = useGLTF('/models/carro.glb').scene
  const modelos: Modelos = {
    predio: useGLTF('/models/predio.glb').scene,
    torre: useGLTF('/models/torre.glb').scene,
    comercio: useGLTF('/models/comercio.glb').scene,
    casa: useGLTF('/models/casa.glb').scene,
    medio: useGLTF('/models/medio.glb').scene,
  }
  const grupo = useRef<Group>(null)
  const corpo = useRef<Group>(null)
  const luz = useRef<PointLight>(null)
  const sRef = useRef(0)
  const rumo = useRef<number | null>(null)
  const inicio = useMemo(() => rua.em(0), [rua])

  useFrame((state, dt) => {
    const delta = Math.min(dt, 0.1) // aba em segundo plano: não deixa o carro "saltar"
    const prog = MathUtils.clamp(viagem.valor, 0, 1)
    const alvo = MathUtils.clamp((prog - INTRO_VIAGEM) / (1 - INTRO_VIAGEM), 0, 1) * rua.comprimento // o carro só anda depois da descida
    const descida = MathUtils.smoothstep(prog, 0, INTRO_VIAGEM) // 0 = vista aérea da largada, 1 = câmera de perseguição
    sRef.current = damp(sRef.current, alvo, 3.5, delta)
    const s = sRef.current
    const c = rua.em(s)
    // Rumo pela corda de ±2 unidades (não pela tangente pontual): curvas fechadas viram giros, não trancos.
    const a = rua.em(s - 2), b = rua.em(s + 2)
    const alvoRumo = Math.atan2(-(b.z - a.z), b.x - a.x) // o carro olha para +X; Y gira +X para (cosθ, -sinθ)
    const antes = rumo.current ?? alvoRumo
    const dif = MathUtils.euclideanModulo(alvoRumo - antes + Math.PI, Math.PI * 2) - Math.PI
    const novo = antes + dif * (1 - Math.exp(-6 * delta))
    rumo.current = novo
    const g = grupo.current
    if (g) {
      g.position.set(c.x, 0, c.z)
      g.rotation.y = novo
    }
    // Inclina na curva: quanto mais rápido o rumo muda, mais a carroceria rola para o lado de fora.
    if (corpo.current) corpo.current.rotation.x = damp(corpo.current.rotation.x, MathUtils.clamp((dif / Math.max(delta, 1e-3)) * 0.012, -0.07, 0.07), 6, delta)
    // Câmera atrás do carro, pelo rumo suavizado: ela "entra" nas curvas um instante depois do carro.
    const tx = Math.cos(novo), tz = -Math.sin(novo)
    const cam = state.camera
    // Tela em pé (celular): o campo de visão horizontal encolhe, então a câmera recua e sobe para o carro caber.
    const recuo = Math.min(2.2, Math.max(1, 1.5 / (state.size.width / state.size.height)))
    const k = 1 - Math.exp(-6 * delta)
    const atras = ATRAS_CAMERA * recuo * descida + 3 * (1 - descida)
    const alto = ALTURA_CAMERA * (0.6 + 0.4 * recuo) * descida + ALTURA_AEREA * (1 - descida)
    cam.position.x += (c.x - tx * atras - tz * 1.1 * descida - cam.position.x) * k
    cam.position.y += (alto - cam.position.y) * k
    cam.position.z += (c.z - tz * atras + tx * 1.1 * descida - cam.position.z) * k
    // Salto de scroll (barra arrastada, âncora): a câmera não fica mais longe do que MAX_CAMERA do carro.
    const dx = cam.position.x - c.x, dz = cam.position.z - c.z, dist = Math.hypot(dx, dz)
    if (dist > MAX_CAMERA) {
      cam.position.x = c.x + (dx / dist) * MAX_CAMERA
      cam.position.z = c.z + (dz / dist) * MAX_CAMERA
    }
    cam.lookAt(c.x + tx * 6 * descida, 0.7 * descida, c.z + tz * 6 * descida)
    luz.current?.position.set(cam.position.x, cam.position.y + 2.5, cam.position.z) // preenchimento: acende o que a câmera vê
  })

  return (
    <>
      <group ref={grupo} position={[inicio.x, 0, inicio.z]}>
        <group ref={corpo}>
          <Clone object={carro} scale={0.7} />
        </group>
        <ContactShadows position={[0, 0.02, 0]} opacity={0.6} scale={6} blur={2.2} far={1.5} resolution={256} />
      </group>
      <pointLight ref={luz} intensity={70} distance={34} decay={2} />
      <Vizinhos predios={predios} sRef={sRef} modelos={modelos} />
    </>
  )
}

/** Câmera inicial: vista aérea sobre a largada (a descida até a perseguição é guiada pelo scroll). */
function posicaoInicial(rua: Caminho): [number, number, number] {
  const c = rua.em(0)
  return [c.x - c.tx * 3, ALTURA_AEREA, c.z - c.tz * 3] // a viagem começa de cima e desce até o carro
}

export function CenaViagem({ rota }: { rota: RotaFeature | undefined }) {
  const rua = useMemo(() => (rota ? criarCaminho(rota.geometry.coordinates) : null), [rota])
  const predios = useMemo(() => (rua ? distribuirPredios(rua) : []), [rua])
  const fundo = useMemo(() => corToken('fundo'), [])
  if (!rua) return null
  return (
    <Canvas dpr={[1, 1.5]} camera={{ fov: 52, near: 0.1, far: 240, position: posicaoInicial(rua) }}>
      <color attach="background" args={[fundo]} />
      <fog attach="fog" args={[fundo, 30, 115]} />
      <hemisphereLight intensity={0.8} />
      <directionalLight position={[20, 40, 10]} intensity={1} />
      <Environment resolution={256}>
        <Lightformer form="rect" intensity={1.5} position={[0, 6, -8]} scale={[16, 4, 1]} />
        <Lightformer form="rect" intensity={0.7} position={[-8, 3, 4]} scale={[6, 3, 1]} />
        <Lightformer form="rect" intensity={0.7} position={[8, 3, 4]} scale={[6, 3, 1]} />
        {/* chão e horizonte claros: sem eles as laterais do carro refletem só o escuro */}
        <Lightformer form="rect" intensity={0.5} position={[0, -3, 0]} rotation-x={Math.PI / 2} scale={[24, 24, 1]} />
        <Lightformer form="rect" intensity={0.7} position={[0, 2, 9]} scale={[20, 3, 1]} />
      </Environment>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.02, 0]}>
        <planeGeometry args={[2400, 2400]} />
        <meshStandardMaterial color={fundo} roughness={1} />
      </mesh>
      <Via rua={rua} />
      <Passeio rua={rua} predios={predios} />
    </Canvas>
  )
}

;['carro', 'predio', 'torre', 'comercio', 'casa', 'medio'].forEach((m) => useGLTF.preload(`/models/${m}.glb`))
