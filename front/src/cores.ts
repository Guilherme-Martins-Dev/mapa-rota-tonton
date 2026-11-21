/** Leitura dos tokens CSS (fonte única: tokens.css) para libs que não entendem var(). */
import type { Criterio } from './data/tipos'

export type RGB = [number, number, number]

/** Valor CSS de um token (ex.: 'texto', 'superficie-2'). */
export function corToken(nome: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(`--${nome}`).trim()
}

/** Token hexadecimal como [r, g, b] (0..255). */
export function corRgb(nome: string): RGB {
  const n = parseInt(corToken(nome).replace('#', ''), 16)
  return Number.isNaN(n) ? [255, 255, 255] : [(n >> 16) & 255, (n >> 8) & 255, n & 255]
}

export const corCriterio = (c: Criterio): RGB => corRgb(`c-${c}`)
