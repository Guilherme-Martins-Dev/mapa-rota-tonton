import type { ButtonHTMLAttributes, ReactNode } from 'react'
import type { Criterio } from '../data/tipos'
import './ui.css'

export const CRITERIOS: { id: Criterio; rotulo: string }[] = [
  { id: 'distancia', rotulo: 'Menor distância' },
  { id: 'tempo', rotulo: 'Menor tempo' },
  { id: 'consumo', rotulo: 'Menor consumo' },
]

export function Cartao({ titulo, children }: { titulo: string; children: ReactNode }) {
  return (
    <article className="cartao">
      <h2>{titulo}</h2>
      <p>{children}</p>
    </article>
  )
}

type MetricaProps = { valor: string; unidade: string; rotulo: string; criterio?: Criterio; melhor?: boolean }

export function Metrica({ valor, unidade, rotulo, criterio, melhor }: MetricaProps) {
  return (
    <div className="metrica" data-criterio={criterio} data-melhor={melhor}>
      <span className="metrica__valor">
        {valor} {unidade}
      </span>
      <span className="metrica__rotulo">{rotulo}</span>
    </div>
  )
}

export function SeletorCriterio({ valor, onChange }: { valor: Criterio; onChange: (c: Criterio) => void }) {
  return (
    <fieldset className="seletor" data-criterio={valor}>
      <legend className="sr-only">Critério da rota</legend>
      {CRITERIOS.map((c) => (
        <label key={c.id} data-criterio={c.id}>
          <input type="radio" name="criterio" value={c.id} checked={valor === c.id} onChange={() => onChange(c.id)} />
          <span>{c.rotulo}</span>
        </label>
      ))}
    </fieldset>
  )
}

export function Botao(props: ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button {...props} className="botao" />
}
