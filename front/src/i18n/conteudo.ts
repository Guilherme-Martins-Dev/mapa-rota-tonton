import { CAPITULOS } from '../conteudo/capitulos'
import { CAPITULOS_EN } from '../conteudo/capitulos.en'
import * as pt from '../conteudo/construcao'
import * as en from '../conteudo/construcao.en'
import { AUTORIA, AUTORIA_EN, CONTEXTO, CONTEXTO_EN, PERFIL_PROFESSOR, PERFIL_PROFESSOR_EN } from '../conteudo/equipe'
import { useIdioma } from './useIdioma'

/** Conteúdo longo (capítulos, página de construção, autoria) no idioma atual. */
export function useConteudo() {
  const { idioma } = useIdioma()
  if (idioma === 'en') {
    return {
      capitulos: CAPITULOS_EN,
      niveis: en.NIVEIS_EN,
      indice: en.INDICE_EN,
      numeros: en.NUMEROS_EN,
      etapas: en.ETAPAS_EN,
      decisoes: en.DECISOES_EN,
      frontTecnicas: en.FRONT_TECNICAS_EN,
      pilha: en.PILHA_EN,
      fontes: en.FONTES_EN,
      limites: en.LIMITES_EN,
      perguntas: en.PERGUNTAS_EN,
      referencias: en.REFERENCIAS_EN,
      comandos: en.COMANDOS_EN,
      autoria: `${AUTORIA_EN} ${PERFIL_PROFESSOR_EN} ${CONTEXTO_EN}`,
    }
  }
  return {
    capitulos: CAPITULOS,
    niveis: pt.NIVEIS,
    indice: pt.INDICE,
    numeros: pt.NUMEROS,
    etapas: pt.ETAPAS,
    decisoes: pt.DECISOES,
    frontTecnicas: pt.FRONT_TECNICAS,
    pilha: pt.PILHA,
    fontes: pt.FONTES,
    limites: pt.LIMITES,
    perguntas: pt.PERGUNTAS,
    referencias: pt.REFERENCIAS,
    comandos: pt.COMANDOS,
    autoria: `${AUTORIA} ${PERFIL_PROFESSOR} ${CONTEXTO}`,
  }
}
