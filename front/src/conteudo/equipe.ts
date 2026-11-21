/** Autoria do projeto. Mesmos nomes e papéis do JSON-LD em index.html: se mudar aqui, mude lá. */
export const AUTOR = 'Guilherme Martins Bezerra'
export const PROFESSOR = 'Sandro Costa Mesquita'
export const COLABORADORES = ['Erick Morais e Silva', 'Kauan Magalhães Costa', 'Luiz Henrique'] as const

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
const colaboradores = lista(COLABORADORES)

export const AUTORIA =
  `Projeto desenvolvido por completo por ${AUTOR}: grafo, algoritmos, back-end, interface e cena 3D. ` +
  `${colaboradores} foram colaboradores do sistema e ajudaram na validação dos dados e dos resultados. Professor responsável: ${PROFESSOR}.`
export const PERFIL_PROFESSOR = `${PROFESSOR} é ${lista(TITULOS_PROFESSOR)}.`
export const CONTEXTO = `Disciplina ${DISCIPLINA}, curso de ${CURSO}, ${INSTITUICAO}. Todos os integrantes da equipe são do curso de ${CURSO}.`

/** Linha de créditos do capítulo final da viagem. */
export const CREDITOS =
  `Desenvolvido por ${AUTOR}. Colaboradores na validação dos dados: ${COLABORADORES.join(', ')}. Professor responsável: ${PROFESSOR}. ` +
  `Disciplina: ${DISCIPLINA}, ${CURSO}, ${INSTITUICAO}.`

// ---- English ----
export const DISCIPLINA_EN = 'Graph Algorithms'
export const CURSO_EN = 'Computer Engineering'
export const INSTITUICAO_EN = 'Centro Universitário Ateneu (UniAteneu), Lagoa campus'

export const TITULOS_PROFESSOR_EN = [
  'coordinator of the technology course at Centro Universitário Ateneu',
  'coordinator of the Postgraduate Program in Artificial Intelligence at UniAteneu',
  'president of ITIA (Institute of Technology and Artificial Intelligence)',
  'a doctoral student at Fiocruz',
] as const

const listaEn = (xs: readonly string[]) => (xs.length > 1 ? `${xs.slice(0, -1).join(', ')} and ${xs[xs.length - 1]}` : xs[0])

export const AUTORIA_EN =
  `Project developed entirely by ${AUTOR}: graph, algorithms, back-end, interface and 3D scene. ` +
  `${listaEn(COLABORADORES)} were collaborators on the system and helped validate the data and the results. Professor in charge: ${PROFESSOR}.`
export const PERFIL_PROFESSOR_EN = `${PROFESSOR} is ${listaEn(TITULOS_PROFESSOR_EN)}.`
export const CONTEXTO_EN = `Course "${DISCIPLINA_EN}" (${DISCIPLINA}), ${CURSO_EN} program, ${INSTITUICAO_EN}. All team members are ${CURSO_EN} students.`
export const CREDITOS_EN =
  `Developed by ${AUTOR}. Collaborators in data validation: ${COLABORADORES.join(', ')}. Professor in charge: ${PROFESSOR}. ` +
  `Course: ${DISCIPLINA_EN}, ${CURSO_EN}, ${INSTITUICAO_EN}.`
