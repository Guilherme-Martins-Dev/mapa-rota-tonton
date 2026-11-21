/** Lê as cores de critério dos tokens CSS (fonte única: tokens.css). */
import type { Criterio } from './data/tipos'

export function corCriterio(c: Criterio): [number, number, number] {
  const hex = getComputedStyle(document.documentElement).getPropertyValue(`--c-${c}`).trim()
  const n = parseInt(hex.replace('#', ''), 16)
  return Number.isNaN(n) ? [255, 255, 255] : [(n >> 16) & 255, (n >> 8) & 255, n & 255]
}

/** Valor CSS de um token (ex.: 'texto', 'superficie-2'), para libs que não leem var(). */
export function corToken(nome: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(`--${nome}`).trim()
}
