import { useThree } from '@react-three/fiber'
import { useEffect } from 'react'

/**
 * Pausa o laço de renderização de um Canvas do R3F enquanto ele não aparece: fora da tela (IntersectionObserver)
 * ou quando `deveRodar()` é falso. Reage ao scroll e acorda sozinho. Cada canvas parado poupa uma passada de WebGL por quadro.
 */
export function usePausa(deveRodar: () => boolean) {
  const gl = useThree((s) => s.gl)
  const setFrameloop = useThree((s) => s.setFrameloop)
  useEffect(() => {
    let visivel = true
    let rodando = true
    const aplicar = () => {
      const r = visivel && deveRodar()
      if (r !== rodando) {
        rodando = r
        setFrameloop(r ? 'always' : 'never')
      }
    }
    const io = new IntersectionObserver(([e]) => {
      visivel = e.isIntersecting
      aplicar()
    })
    io.observe(gl.domElement)
    window.addEventListener('scroll', aplicar, { passive: true })
    aplicar()
    return () => {
      io.disconnect()
      window.removeEventListener('scroll', aplicar)
      setFrameloop('always')
    }
  }, [gl, setFrameloop, deveRodar])
}

export const reduzMovimento = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches
