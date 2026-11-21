import { useEffect, useState } from 'react'
import { carregarRotas, type Rotas } from './tipos'

export type EstadoRotas = { estado: 'carregando' } | { estado: 'erro' } | { estado: 'pronto'; rotas: Rotas }

export function useRotas(url?: string): EstadoRotas {
  const [s, setS] = useState<EstadoRotas>({ estado: 'carregando' })
  useEffect(() => {
    let vivo = true
    carregarRotas(url).then((rotas) => vivo && setS(rotas ? { estado: 'pronto', rotas } : { estado: 'erro' }))
    return () => {
      vivo = false
    }
  }, [url])
  return s
}
