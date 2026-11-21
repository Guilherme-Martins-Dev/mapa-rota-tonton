import { useEffect, useMemo, useState } from 'react'
import type { Nivel } from '../conteudo/construcao'
import { useConteudo } from '../i18n/conteudo'
import { useT } from '../i18n/useIdioma'
import { Tx } from '../ui/Tx'
import './construcao.css'

/** Só no desktop, onde o índice e a resposta ficam fixos: ali a leitura acompanha a rolagem. */
const desktop = () => window.matchMedia('(min-width: 960px)').matches

/** Página de construção: como o projeto foi feito, com fontes, licenças e perguntas e respostas por nível. */
export default function Construcao() {
  const t = useT()
  const { niveis: NIVEIS, indice: INDICE, numeros: NUMEROS, etapas: ETAPAS, decisoes: DECISOES, frontTecnicas: FRONT_TECNICAS, pilha: PILHA,
    fontes: FONTES, limites: LIMITES, perguntas: PERGUNTAS, referencias: REFERENCIAS, comandos: COMANDOS, autoria } = useConteudo()
  const rotuloNivel = (n: Nivel) => NIVEIS.find((x) => x.id === n)?.rotulo
  const [nivel, setNivel] = useState<Nivel | 'todos'>('todos')
  const [sel, setSel] = useState(0)
  const lista = useMemo(() => PERGUNTAS.filter((q) => nivel === 'todos' || q.nivel === nivel), [nivel, PERGUNTAS])
  const atual = lista[Math.min(sel, lista.length - 1)]
  const contagem = (n: Nivel) => PERGUNTAS.filter((q) => q.nivel === n).length
  const [secao, setSecao] = useState<string>(INDICE[0].id)

  // Seção em foco: a que cruza a faixa de leitura (um terço superior da janela).
  useEffect(() => {
    if (!desktop()) return
    const io = new IntersectionObserver(
      (es) => es.forEach((e) => e.isIntersecting && setSecao(e.target.id)),
      { rootMargin: '-20% 0px -70% 0px' },
    )
    INDICE.forEach((i) => { const el = document.getElementById(i.id); if (el) io.observe(el) })
    return () => io.disconnect()
  }, [INDICE])

  // Pergunta em foco: a resposta fixa troca conforme a lista passa pela faixa de leitura.
  useEffect(() => {
    if (!desktop()) return
    const io = new IntersectionObserver(
      (es) => es.forEach((e) => { if (e.isIntersecting) setSel(Number((e.target as HTMLElement).dataset.i)) }),
      { rootMargin: '-35% 0px -55% 0px' },
    )
    document.querySelectorAll('.constr__perguntas li').forEach((el) => io.observe(el))
    return () => io.disconnect()
  }, [lista])

  const filtrar = (n: Nivel | 'todos') => {
    setNivel(n)
    setSel(0)
  }

  return (
    <main className="constr">
      <nav className="constr__indice" aria-label={t('constrNav')}>
        <ol>
          {INDICE.map((i) => (
            <li key={i.id}><a href={`#${i.id}`} aria-current={secao === i.id ? 'location' : undefined}>{i.rotulo}</a></li>
          ))}
        </ol>
      </nav>

      <div className="constr__corpo">
        <header id="resumo">
          <h1>{t('constrTitulo')}</h1>
          <p className="constr__lead">{t('constrLead')}</p>
          <p className="constr__lead">{autoria}</p>
          <dl className="constr__numeros">
            {NUMEROS.map((n) => (
              <div key={n.rotulo}>
                <dd>{n.valor}</dd>
                <dt>{n.rotulo}</dt>
              </div>
            ))}
          </dl>
        </header>

        <section id="arquitetura" aria-labelledby="t-arq">
          <h2 id="t-arq">{t('constrArq')}</h2>
          <ol className="constr__etapas">
            {ETAPAS.map((e) => (
              <li key={e.titulo}>
                <h3>{e.titulo}</h3>
                <p>{e.texto}</p>
              </li>
            ))}
          </ol>
        </section>

        <section id="back" aria-labelledby="t-back">
          <h2 id="t-back">{t('constrBack')}</h2>
          <p className="constr__intro">{t('constrBackIntro')}</p>
          <table className="constr__tabela">
            <thead>
              <tr><th scope="col">{t('constrDecisao')}</th><th scope="col">{t('constrResultado')}</th><th scope="col">{t('constrDocumento')}</th></tr>
            </thead>
            <tbody>
              {DECISOES.map((d) => (
                <tr key={d.doc}>
                  <th scope="row">{d.titulo}</th>
                  <td>{d.resumo}</td>
                  <td><code>{d.doc.replace('docs/decisoes/', '')}</code></td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section id="front" aria-labelledby="t-front">
          <h2 id="t-front">{t('constrFront')}</h2>
          <dl className="constr__lista">
            {FRONT_TECNICAS.map((t) => (
              <div key={t.titulo}>
                <dt>{t.titulo}</dt>
                <dd><Tx>{t.texto}</Tx></dd>
              </div>
            ))}
          </dl>
          <h3 className="constr__sub">{t('constrPilha')}</h3>
          <dl className="constr__lista">
            {PILHA.map(([k, v]) => (
              <div key={k}>
                <dt>{k}</dt>
                <dd>{v}</dd>
              </div>
            ))}
          </dl>
        </section>

        <section id="dados" aria-labelledby="t-dados">
          <h2 id="t-dados">{t('constrDados')}</h2>
          <dl className="constr__lista">
            {FONTES.map((f) => (
              <div key={f.nome}>
                <dt>{f.nome}<span>{f.licenca}</span></dt>
                <dd>{f.uso}. {f.nota}</dd>
              </div>
            ))}
          </dl>
        </section>

        <section id="limites" aria-labelledby="t-lim">
          <h2 id="t-lim">{t('constrLimites')}</h2>
          <ul className="constr__limites">
            {LIMITES.map((l) => (
              <li key={l}>{l}</li>
            ))}
          </ul>
        </section>

        <section id="perguntas" aria-labelledby="t-perg">
          <h2 id="t-perg">{t('constrPerguntas')}</h2>
          <div className="constr__filtro" role="group" aria-label={t('constrFiltro')}>
            <button type="button" aria-pressed={nivel === 'todos'} onClick={() => filtrar('todos')}>{t('constrTodas')} {PERGUNTAS.length}</button>
            {NIVEIS.map((n) => (
              <button key={n.id} type="button" aria-pressed={nivel === n.id} onClick={() => filtrar(n.id)}>
                {n.rotulo} {contagem(n.id)}
              </button>
            ))}
          </div>
          <div className="constr__qa">
            <ul className="constr__perguntas">
              {lista.map((q, i) => (
                <li key={q.p} data-i={i}>
                  <button type="button" aria-expanded={i === sel} onClick={() => setSel(i)}>
                    <span><Tx>{q.p}</Tx></span>
                    {nivel === 'todos' && <small>{rotuloNivel(q.nivel)}</small>}
                  </button>
                  {i === sel && <p className="constr__inline"><Tx>{q.r}</Tx></p>}
                </li>
              ))}
            </ul>
            {atual && (
              <div className="constr__resposta" aria-live="polite">
                <small>{rotuloNivel(atual.nivel)}</small>
                <h3><Tx>{atual.p}</Tx></h3>
                <p><Tx>{atual.r}</Tx></p>
              </div>
            )}
          </div>
        </section>

        <section id="referencias" aria-labelledby="t-ref">
          <h2 id="t-ref">{t('constrRefs')}</h2>
          <ol className="constr__refs">
            {REFERENCIAS.map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ol>
        </section>

        <section id="reproduzir" aria-labelledby="t-rep">
          <h2 id="t-rep">{t('constrRepro')}</h2>
          <p className="constr__intro">{t('constrReproIntro')}</p>
          <dl className="constr__lista">
            {COMANDOS.map((c) => (
              <div key={c.cmd}>
                <dt>{c.rotulo}</dt>
                <dd><code>{c.cmd}</code></dd>
              </div>
            ))}
          </dl>
        </section>
      </div>
    </main>
  )
}
