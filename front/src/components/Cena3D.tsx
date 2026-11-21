import { Environment, Lightformer, useGLTF } from '@react-three/drei'
import { Canvas, useFrame } from '@react-three/fiber'
import { useRef } from 'react'
import type { Group } from 'three'
import { MathUtils } from 'three'
import { CARRO_GLB as CARRO } from '../cena/modelos'
import { Chao } from '../cena/Chao'
import { usePausa, reduzMovimento } from '../cena/pausa'
import { MERGULHO, progresso, viagem } from '../cena/progresso'
import { corToken } from '../cores'


/** Carro: gira com o scroll. */
function Carro() {
  const ref = useRef<Group>(null)
  const { scene } = useGLTF(CARRO)
  useFrame((_, dt) => {
    const g = ref.current
    if (!g) return
    const p = progresso.valor
    g.rotation.y = MathUtils.damp(g.rotation.y, -0.6 + p * Math.PI * 2, 4, dt)
  })
  return <primitive ref={ref} object={scene} scale={0.55} position={[0, -0.6, 0]} />
}

/** O carro do hero só aparece até o fim do mergulho; depois disso o canvas para. */
const heroVisivel = () => reduzMovimento() || viagem.valor < MERGULHO + 0.02

function Pausa() {
  usePausa(heroVisivel)
  return null
}

export function Cena3D() {
  return (
    <Canvas camera={{ position: [0, 1.2, 6], fov: 40 }} dpr={[1, 2]} aria-hidden="true">
      <hemisphereLight args={[corToken('texto'), corToken('superficie-2'), 0.4]} />
      <directionalLight position={[4, 6, 3]} intensity={1.6} />
      {/* Reflexos: ambiente gerado localmente (sem baixar HDRI) com três painéis de luz. */}
      <Environment resolution={256}>
        <Lightformer form="rect" intensity={3} position={[0, 5, -6]} scale={[12, 4, 1]} />
        <Lightformer form="rect" intensity={2} position={[-6, 1, 2]} scale={[2, 6, 1]} />
        <Lightformer form="rect" intensity={1.5} position={[6, 2, 3]} scale={[2, 5, 1]} />
      </Environment>
      <Pausa />
      <Chao />
      <Carro />
    </Canvas>
  )
}

useGLTF.preload(CARRO)
