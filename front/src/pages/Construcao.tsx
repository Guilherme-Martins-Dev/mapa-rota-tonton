import { useMemo, useState } from 'react'
import {
  COMANDOS, DECISOES, ETAPAS, FONTES, FRONT_TECNICAS, INDICE, LIMITES, NIVEIS, NUMEROS, PERGUNTAS, PILHA, REFERENCIAS,
  type Nivel,
} from '../conteudo/construcao'
import './construcao.css'

/** Página de construção: como o projeto foi feito, com fontes, licenças e perguntas e respostas por nível. */
export default function Construcao() {
  const [nivel, setNivel] = useState<Nivel | 'todos'>('todos')
  const [aberto, setAberto] = useState(false)
  const lista = useMemo(() => PERGUNTAS.filter((q) => nivel === 'todos' || q.nivel === nivel), [nivel])
  const contagem = (n: Nivel) => PERGUNTAS.filter((q) => q.nivel === n).length

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
            Um sistema que escolhe rotas em Messejana, Fortaleza, por distância, tempo ou consumo de combustível, e um site que mostra como ele
            pensa. Esta página reúne o caminho completo, as fontes, as licenças e as respostas que um professor pode pedir, do básico ao avançado.
          </p>
          <dl className="constr__numeros">
            {NUMEROS.map((n) => (
              <div key={n.rotulo}>
                <dt>{n.rotulo}</dt>
                <dd>{n.valor}</dd>
              </div>
            ))}
          </dl>
        </header>

        <section id="arquitetura" aria-labelledby="t-arq">
          <h2 id="t-arq">Arquitetura</h2>
          <p>Do mapa colaborativo ao navegador, em seis etapas.</p>
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
          <h2 id="t-back">Back-end: decisões e medições</h2>
          <p>
            Cada decisão importante tem um documento no repositório, com o que foi medido e o que ficou como hipótese. Os números abaixo vêm
            desses documentos.
          </p>
          <ul className="constr__decisoes">
            {DECISOES.map((d) => (
              <li key={d.doc}>
                <h3>{d.titulo}</h3>
                <p>{d.resumo}</p>
                <code>{d.doc}</code>
              </li>
            ))}
          </ul>
        </section>

        <section id="front" aria-labelledby="t-front">
          <h2 id="t-front">Front-end: técnicas e ferramentas</h2>
          <ul className="constr__tecnicas">
            {FRONT_TECNICAS.map((t) => (
              <li key={t.titulo}>
                <h3>{t.titulo}</h3>
                <p>{t.texto}</p>
              </li>
            ))}
          </ul>
          <table className="constr__tabela">
            <caption>Pilha de tecnologia (versões do package.json e do pyproject.toml)</caption>
            <tbody>
              {PILHA.map(([k, v]) => (
                <tr key={k}>
                  <th scope="row">{k}</th>
                  <td>{v}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section id="dados" aria-labelledby="t-dados">
          <h2 id="t-dados">Dados, modelos e licenças</h2>
          <p>O que cada fonte entrega, sob qual licença e o que o projeto fez com ela.</p>
          <ul className="constr__fontes">
            {FONTES.map((f) => (
              <li key={f.nome}>
                <h3>{f.nome}</h3>
                <p>{f.uso}. <strong>Licença:</strong> {f.licenca}.</p>
                {f.nota && <p>{f.nota}</p>}
              </li>
            ))}
          </ul>
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
            <button type="button" aria-pressed={nivel === 'todos'} onClick={() => setNivel('todos')}>
              Todas ({PERGUNTAS.length})
            </button>
            {NIVEIS.map((n) => (
              <button key={n.id} type="button" aria-pressed={nivel === n.id} onClick={() => setNivel(n.id)}>
                {n.rotulo} ({contagem(n.id)})
              </button>
            ))}
          </div>
          <div className="constr__acoes">
            <button type="button" className="constr__alternar" onClick={() => setAberto((a) => !a)}>
              {aberto ? 'Recolher todas' : 'Abrir todas'}
            </button>
          </div>
          <div className="constr__perguntas">
            {lista.map((q) => (
              <details key={`${aberto}-${q.p}`} open={aberto}>
                <summary>
                  <span className="constr__nivel" data-nivel={q.nivel}>{NIVEIS.find((n) => n.id === q.nivel)?.rotulo}</span>
                  {q.p}
                </summary>
                <p>{q.r}</p>
              </details>
            ))}
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
          <p>Com Python 3 e Node instalados, na raiz do repositório:</p>
          <dl className="constr__comandos">
            {COMANDOS.map((c) => (
              <div key={c.cmd}>
                <dt>{c.rotulo}</dt>
                <dd><code>{c.cmd}</code></dd>
              </div>
            ))}
          </dl>
          <p>A chave da TomTom, se usada, fica num arquivo .env que não vai para o repositório.</p>
        </section>
      </div>
    </main>
  )
}
