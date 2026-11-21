import { useEffect } from 'react'
import { AUTOR, COLABORADORES, CURSO, CURSO_EN, PROFESSOR } from '../conteudo/equipe'
import { useConteudo } from '../i18n/conteudo'
import { useIdioma, useT } from '../i18n/useIdioma'
import { Tx } from '../ui/Tx'

/** Texto puro de uma frase com fórmulas $...$ (para os dados estruturados). */
const semTex = (s: string) => s.replace(/\$([^$]*)\$/g, (_, m: string) => m.replace(/\\[a-zA-Z]+/g, '').replace(/[{}\\]/g, '')).replace(/\s+/g, ' ').trim()

/**
 * Conteúdo fora da vista, para buscadores e leitores de tela: é o mesmo que o site já mostra (capítulos, perguntas e respostas,
 * fontes e autoria), em texto corrido e no idioma atual, mais o FAQPage em JSON-LD. Não acrescenta nada que o visitante não possa ler.
 */
export function ConteudoOculto() {
  const t = useT()
  const { idioma } = useIdioma()
  const { capitulos, fontes, autoria } = useConteudo()
  const pt = idioma === 'pt'
  const curso = pt ? CURSO : CURSO_EN

  useEffect(() => {
    const el = document.createElement('script')
    el.type = 'application/ld+json'
    el.id = 'faq-jsonld'
    el.textContent = JSON.stringify({
      '@context': 'https://schema.org',
      '@type': 'FAQPage',
      inLanguage: pt ? 'pt-BR' : 'en',
      mainEntity: capitulos.flatMap((c) =>
        c.perguntas.map((q) => ({
          '@type': 'Question',
          name: semTex(q.p),
          acceptedAnswer: { '@type': 'Answer', text: semTex(q.r) },
        })),
      ),
    })
    document.head.append(el)
    return () => el.remove()
  }, [capitulos, pt])

  return (
    <footer className="sr-only" aria-label={pt ? 'Resumo, fontes e créditos' : 'Summary, sources and credits'}>
      <h2>{t('marca')}</h2>
      <p>{t('descricao')}</p>
      <h2>{pt ? 'A viagem pelo projeto' : 'The journey through the project'}</h2>
      {capitulos.map((c) => (
        <section key={c.id}>
          <h3>{c.titulo}</h3>
          <p><Tx>{c.texto}</Tx></p>
          <dl>
            {c.perguntas.map((q) => (
              <div key={q.p}>
                <dt><Tx>{q.p}</Tx></dt>
                <dd><Tx>{q.r}</Tx></dd>
              </div>
            ))}
          </dl>
        </section>
      ))}
      <h2>{pt ? 'Fontes e licenças' : 'Sources and licenses'}</h2>
      <ul>
        {fontes.map((f) => (
          <li key={f.nome}>{f.nome} ({f.licenca}): {f.uso}. {f.nota}</li>
        ))}
      </ul>
      <h2>{pt ? 'Autoria e créditos' : 'Authorship and credits'}</h2>
      <p>{autoria}</p>
      <ul>
        <li>{AUTOR}: {pt ? 'desenvolvedor do projeto' : 'project developer'}, {curso}.</li>
        {COLABORADORES.map((c) => (
          <li key={c}>{c}: {pt ? 'colaborador na validação dos dados' : 'data-validation collaborator'}, {curso}.</li>
        ))}
        <li>{PROFESSOR}: {pt ? 'professor responsável' : 'professor in charge'}.</li>
      </ul>
    </footer>
  )
}
