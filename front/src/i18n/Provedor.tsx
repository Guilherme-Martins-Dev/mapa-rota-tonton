import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { CHAVE_IDIOMA, IdiomaContexto, idiomaInicial, type Idioma } from './useIdioma'
import { UI } from './ui'

/** Guarda o idioma, ajusta <html lang>, o título e a descrição da página (o texto das telas vem de useT e do conteúdo por idioma). */
export function IdiomaProvedor({ children }: { children: ReactNode }) {
  const [idioma, setEstado] = useState<Idioma>(idiomaInicial)
  const valor = useMemo(
    () => ({
      idioma,
      setIdioma: (i: Idioma) => {
        setEstado(i)
        try {
          localStorage.setItem(CHAVE_IDIOMA, i)
        } catch {
          /* vale só para esta visita */
        }
      },
    }),
    [idioma],
  )
  useEffect(() => {
    document.documentElement.lang = idioma === 'en' ? 'en' : 'pt-BR'
    document.title = UI[idioma].titulo
    document.querySelector('meta[name="description"]')?.setAttribute('content', UI[idioma].descricao)
  }, [idioma])
  return <IdiomaContexto.Provider value={valor}>{children}</IdiomaContexto.Provider>
}
