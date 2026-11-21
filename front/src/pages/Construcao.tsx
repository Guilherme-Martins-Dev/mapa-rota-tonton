import { useMemo, useState } from 'react'
import {
  COMANDOS, DECISOES, ETAPAS, FONTES, FRONT_TECNICAS, INDICE, LIMITES, NIVEIS, NUMEROS, PERGUNTAS, PILHA, REFERENCIAS,
  type Nivel,
} from '../conteudo/construcao'
import './construcao.css'

const rotuloNivel = (n: Nivel) => NIVEIS.find((x) => x.id === n)?.rotulo

/** Página de construção: como o projeto foi feito, com fontes, licenças e perguntas e respostas por nível. */
export default function Construcao() {
  const [nivel, setNivel] = useState<Nivel | 'todos'>('todos')
  const [sel, setSel] = useState(0)
  const lista = useMemo(() => PERGUNTAS.filter((q) => nivel === 'todos' || q.nivel === nivel), [nivel])
  const atual = lista[Math.min(sel, lista.length - 1)]
  const contagem = (n: Nivel) => PERGUNTAS.filter((q) => q.nivel === n).length
  const filtrar = (n: Nivel | 'todos') => {
    setNivel(n)
    setSel(0)
  }

  return (
    <main className="constr">
      <nav className="constr__indice" aria-label="Nesta página">
        <ol>
          {INDICE.map((i) => (
            <li key={i.id}><a href={`#${i.id}`}>{i.rotulo}</a></li>
          ))}
        </ol>
      </nav>

      <div className="constr__corpo">
        <header id="resumo">
          <h1>Como este site foi construído</h1>
          <p className="constr__lead">
            O sistema escolhe rotas em Messejana, Fortaleza, por distância, tempo ou consumo de combustível. O site mostra, passo a passo, como
            ele decide. Aqui estão o caminho, as fontes, as licenças e as respostas para perguntas do básico ao avançado.
          </p>
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
          <h2 id="t-arq">Do mapa ao navegador</h2>
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
          <h2 id="t-back">Back-end: o que foi decidido e medido</h2>
          <p className="constr__intro">Cada decisão tem um documento no repositório. Os números abaixo vêm deles.</p>
          <table className="constr__tabela">
            <thead>
              <tr><th scope="col">Decisão</th><th scope="col">Resultado</th><th scope="col">Documento</th></tr>
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
          <h2 id="t-front">Front-end: técnicas</h2>
          <dl className="constr__lista">
            {FRONT_TECNICAS.map((t) => (
              <div key={t.titulo}>
                <dt>{t.titulo}</dt>
                <dd>{t.texto}</dd>
              </div>
            ))}
          </dl>
          <h3 className="constr__sub">Pilha</h3>
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
          <h2 id="t-dados">Dados, modelos e licenças</h2>
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
          <h2 id="t-lim">O que o projeto não garante</h2>
          <ul className="constr__limites">
            {LIMITES.map((l) => (
              <li key={l}>{l}</li>
            ))}
          </ul>
        </section>

        <section id="perguntas" aria-labelledby="t-perg">
          <h2 id="t-perg">Perguntas e respostas</h2>
          <div className="constr__filtro" role="group" aria-label="Filtrar por nível">
            <button type="button" aria-pressed={nivel === 'todos'} onClick={() => filtrar('todos')}>Todas {PERGUNTAS.length}</button>
            {NIVEIS.map((n) => (
              <button key={n.id} type="button" aria-pressed={nivel === n.id} onClick={() => filtrar(n.id)}>
                {n.rotulo} {contagem(n.id)}
              </button>
            ))}
          </div>
          <div className="constr__qa">
            <ul className="constr__perguntas">
              {lista.map((q, i) => (
                <li key={q.p}>
                  <button type="button" aria-expanded={i === sel} onClick={() => setSel(i)}>
                    <span>{q.p}</span>
                    {nivel === 'todos' && <small>{rotuloNivel(q.nivel)}</small>}
                  </button>
                  {i === sel && <p className="constr__inline">{q.r}</p>}
                </li>
              ))}
            </ul>
            {atual && (
              <div className="constr__resposta" aria-live="polite">
                <small>{rotuloNivel(atual.nivel)}</small>
                <h3>{atual.p}</h3>
                <p>{atual.r}</p>
              </div>
            )}
          </div>
        </section>

        <section id="referencias" aria-labelledby="t-ref">
          <h2 id="t-ref">Referências</h2>
          <ol className="constr__refs">
            {REFERENCIAS.map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ol>
        </section>

        <section id="reproduzir" aria-labelledby="t-rep">
          <h2 id="t-rep">Como reproduzir</h2>
          <p className="constr__intro">Com Python 3 e Node instalados, na raiz do repositório. A chave da TomTom, se usada, fica num .env fora do repositório.</p>
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
