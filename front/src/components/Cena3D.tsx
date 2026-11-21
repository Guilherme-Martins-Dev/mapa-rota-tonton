import { Canvas, useFrame } from '@react-three/fiber'
import { useRef } from 'react'
import type { Mesh } from 'three'

/** Placeholder da cena 3D (Fase 4 troca por modelos reais .glb). */
function Peca() {
  const ref = useRef<Mesh>(null)
  useFrame((_, dt) => {
    if (ref.current) ref.current.rotation.y += dt * 0.4
  })
  return (
    <mesh ref={ref}>
      <icosahedronGeometry args={[1, 1]} />
      <meshStandardMaterial color="#ffbe3c" flatShading />
    </mesh>
  )
}

export function Cena3D() {
  return (
    <Canvas camera={{ position: [0, 0, 4] }} dpr={[1, 2]} aria-hidden="true">
      <ambientLight intensity={0.6} />
      <directionalLight position={[3, 3, 3]} />
      <Peca />
    </Canvas>
  )
}
