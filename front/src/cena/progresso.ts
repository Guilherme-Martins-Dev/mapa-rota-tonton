/** Progresso do scroll (0..1) lido pelo useFrame do R3F sem re-render do React. */
export const progresso = { valor: 0 }

/** Progresso da seção pinada da viagem (0 = largada, 1 = chegada). */
export const viagem = { valor: 0 }

/** Fatia inicial do progresso da viagem usada para a câmera descer da vista aérea até o carro; o carro só anda depois dela. */
export const INTRO_VIAGEM = 0.17

/** Fatia do progresso da viagem em que o mapa mergulha até a largada: zoom, inclinação, carro do hero ao centro e a cena da rua aparece. */
export const MERGULHO = 0.1
