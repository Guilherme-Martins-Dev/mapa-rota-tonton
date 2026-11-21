import type { ButtonHTMLAttributes, ReactNode } from 'react'
import type { Criterio } from '../data/tipos'
import { useT } from '../i18n/useIdioma'
import './ui.css'

/** Os três critérios, com o rótulo no idioma atual. */
export function useCriterios(): { id: Criterio; rotulo: string }[] {
  const t = useT()
  return [
    { id: 'distancia', rotulo: t('critDistancia') },
    { id: 'tempo', rotulo: t('critTempo') },
    { id: 'consumo', rotulo: t('critConsumo') },
  ]
}

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
  const t = useT()
  const criterios = useCriterios()
  return (
    <fieldset className="seletor" data-criterio={valor}>
      <legend className="sr-only">{t('critLegenda')}</legend>
      {criterios.map((c) => (
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
