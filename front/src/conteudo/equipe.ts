/** Autoria do projeto. Mesmos nomes e papéis do JSON-LD em index.html: se mudar aqui, mude lá. */
export const AUTOR = 'Guilherme Martins Bezerra'
export const PROFESSOR = 'Sandro Costa Mesquita'
export const COLABORADORES = ['Erick Morais e Silva', 'Kauan Magalhães Costa', 'Luiz Henrique'] as const

export const AUTORIA =
  `Projeto desenvolvido por completo por ${AUTOR}: grafo, algoritmos, back-end, interface e cena 3D. ` +
  `${COLABORADORES.slice(0, -1).join(', ')} e ${COLABORADORES[COLABORADORES.length - 1]} foram colaboradores do sistema e ` +
  `ajudaram na validação dos dados e dos resultados. Professor responsável: ${PROFESSOR}.`

export const DISCIPLINA = 'Algoritmos em Grafos'
export const CURSO = 'Engenharia da Computação'
export const INSTITUICAO = 'Centro Universitário Ateneu (UniAteneu), unidade Lagoa'

/** Titulação e funções do professor responsável (informadas pelo autor). */
export const TITULOS_PROFESSOR = [
  'coordenador do curso de tecnologia no Centro Universitário Ateneu',
  'coordenador da Pós-graduação em Inteligência Artificial da UniAteneu',
  'presidente do ITIA (Instituto de Tecnologia e Inteligência Artificial)',
  'doutorando na Fiocruz',
] as const

const lista = (xs: readonly string[]) => (xs.length > 1 ? `${xs.slice(0, -1).join(', ')} e ${xs[xs.length - 1]}` : xs[0])
export const PERFIL_PROFESSOR = `${PROFESSOR} é ${lista(TITULOS_PROFESSOR)}.`
export const CONTEXTO = `Disciplina ${DISCIPLINA}, curso de ${CURSO}, ${INSTITUICAO}. Todos os integrantes da equipe são do curso de ${CURSO}.`

/** Linha de créditos do capítulo final da viagem. */
export const CREDITOS =
  `Desenvolvido por ${AUTOR}. Colaboradores na validação dos dados: ${COLABORADORES.join(', ')}. Professor responsável: ${PROFESSOR}. ` +
  `Disciplina: ${DISCIPLINA}, ${CURSO}, ${INSTITUICAO}.`
