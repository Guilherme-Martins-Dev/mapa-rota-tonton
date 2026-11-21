import { useSyncExternalStore } from 'react'
import { EVENTO_TEMA, trocarTemaComCarro, type Tema } from './carro'

export type { Tema }
export const CHAVE_TEMA = 'tonton.tema'

export const temaAtual = (): Tema => (document.documentElement.dataset.theme === 'light' ? 'light' : 'dark')

/** Tema vigente como estado do React: quem lê tokens de cor (mapa, cena 3D) rerenderiza quando ele muda. */
export function useTema(): Tema {
  return useSyncExternalStore(
    (aviso) => {
      window.addEventListener(EVENTO_TEMA, aviso)
      return () => window.removeEventListener(EVENTO_TEMA, aviso)
    },
    temaAtual,
    () => 'dark',
  )
}

const COR_BARRA: Record<Tema, string> = { dark: '#0a0e14', light: '#f6f4ef' } // barra do navegador no celular

/** Aplica o tema no <html>, guarda a escolha e avisa os ouvintes (o armazenamento pode estar bloqueado). */
export function aplicarTema(tema: Tema): void {
  document.documentElement.dataset.theme = tema
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', COR_BARRA[tema])
  try {
    localStorage.setItem(CHAVE_TEMA, tema)
  } catch {
    /* sem armazenamento: vale só para esta visita */
  }
  window.dispatchEvent(new CustomEvent<Tema>(EVENTO_TEMA, { detail: tema }))
}

/** Alterna claro/escuro com o carro derrapando pela tela. */
export function alternarTema(): Promise<void> {
  return trocarTemaComCarro(() => aplicarTema(temaAtual() === 'dark' ? 'light' : 'dark'))
}
