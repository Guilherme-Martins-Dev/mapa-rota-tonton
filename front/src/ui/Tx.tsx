import katex from 'katex'
import 'katex/dist/katex.min.css'
import { Fragment, useMemo } from 'react'

/** Texto com fórmulas em LaTeX entre cifrões: "o custo é $O((V+E)\log V)$" vira texto com a fórmula composta pelo KaTeX. */
export function Tx({ children }: { children: string }) {
  const partes = useMemo(
    () =>
      children.split(/\$([^$]+)\$/g).map((trecho, i) =>
        i % 2 === 0 ? trecho : katex.renderToString(trecho, { throwOnError: false, output: 'htmlAndMathml' }),
      ),
    [children],
  )
  return (
    <>
      {partes.map((t, i) =>
        i % 2 === 0 ? <Fragment key={i}>{t}</Fragment> : <span key={i} className="tx" dangerouslySetInnerHTML={{ __html: t }} />,
      )}
    </>
  )
}
