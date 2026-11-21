/** Progresso do scroll (0..1) lido pelo useFrame do R3F sem re-render do React. */
export const progresso = { valor: 0 }

/** Progresso da seção pinada da viagem (0 = largada, 1 = chegada). */
export const viagem = { valor: 0 }

/** Fatia inicial do progresso da viagem usada para a câmera descer da vista aérea até o carro; o carro só anda depois dela. */
export const INTRO_VIAGEM = 0.06
