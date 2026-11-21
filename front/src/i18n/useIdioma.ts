import { createContext, useContext } from 'react'
import { UI, type ChaveUi } from './ui'

export type Idioma = 'pt' | 'en'
export const CHAVE_IDIOMA = 'tonton.idioma'

export const IdiomaContexto = createContext<{ idioma: Idioma; setIdioma: (i: Idioma) => void }>({ idioma: 'pt', setIdioma: () => {} })

export const useIdioma = () => useContext(IdiomaContexto)

/** Texto da interface no idioma atual; chaves com valor função recebem os argumentos. */
export function useT() {
  const { idioma } = useIdioma()
  return <K extends ChaveUi>(chave: K): (typeof UI)['pt'][K] => UI[idioma][chave]
}

/** Número com casas fixas e o separador decimal do idioma (vírgula em português, ponto em inglês). */
export function useFmt() {
  const { idioma } = useIdioma()
  return (n: number, casas: number) => n.toFixed(casas).replace('.', idioma === 'pt' ? ',' : '.')
}

/** Idioma inicial: o último escolhido; senão o do navegador (inglês só se ele for inglês). */
export function idiomaInicial(): Idioma {
  try {
    const salvo = localStorage.getItem(CHAVE_IDIOMA)
    if (salvo === 'pt' || salvo === 'en') return salvo
  } catch {
    /* sem armazenamento */
  }
  return navigator.language?.toLowerCase().startsWith('en') ? 'en' : 'pt'
}
