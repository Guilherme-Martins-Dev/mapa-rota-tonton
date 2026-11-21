import { useFrame } from '@react-three/fiber'
import { useMemo, useRef } from 'react'
import { Color, ShaderMaterial } from 'three'
import { corToken } from '../cores'
import { progresso } from './progresso'

const VERT = /* glsl */ `
varying vec2 vUv;
void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }
`

// Grade de "ruas": linhas finas, nós nos cruzamentos e um pulso radial que avança com o scroll.
const FRAG = /* glsl */ `
precision highp float;
varying vec2 vUv;
uniform float uTempo;
uniform float uProgresso;
uniform vec3 uCor;
void main() {
  vec2 p = vUv * 12.0;
  vec2 f = abs(fract(p - 0.5) - 0.5) / fwidth(p);
  float linha = 1.0 - min(min(f.x, f.y), 1.0);
  float no = smoothstep(0.12, 0.0, length(fract(p) - 0.5) - 0.0) ;
  float d = distance(vUv, vec2(0.5));
  float pulso = smoothstep(0.06, 0.0, abs(d - fract(uTempo * 0.15 + uProgresso) * 0.7));
  float borda = smoothstep(0.48, 0.1, d);
  float a = (linha * 0.35 + no * 0.5 + pulso * 0.8) * borda;
  gl_FragColor = vec4(uCor, a);
}
`

/** Chão com shader: o grafo viário abstrato sob o carro. */
export function Chao() {
  const mat = useRef<ShaderMaterial>(null)
  const uniforms = useMemo(
    () => ({ uTempo: { value: 0 }, uProgresso: { value: 0 }, uCor: { value: new Color(corToken('c-distancia')) } }),
    [],
  )
  useFrame((_, dt) => {
    if (!mat.current) return
    mat.current.uniforms.uTempo.value += dt
    mat.current.uniforms.uProgresso.value = progresso.valor
  })
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.62, -0.4]}>
      <planeGeometry args={[6.4, 6.4]} />
      <shaderMaterial ref={mat} vertexShader={VERT} fragmentShader={FRAG} uniforms={uniforms} transparent depthWrite={false} />
    </mesh>
  )
}
