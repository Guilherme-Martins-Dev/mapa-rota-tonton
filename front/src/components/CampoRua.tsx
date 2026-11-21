import { useEffect, useId, useRef, useState } from 'react'
import { buscarRuas } from '../data/api'

type Props = { rotulo: string; valor: string; onChange: (v: string) => void; placeholder?: string }

/** Combobox ARIA: digita, a API sugere ruas do grafo; setas, Enter e Esc funcionam. Também aceita "lat,lon". */
export function CampoRua({ rotulo, valor, onChange, placeholder }: Props) {
  const id = useId()
  const [sugestoes, setSugestoes] = useState<string[]>([])
  const [aberto, setAberto] = useState(false)
  const [ativo, setAtivo] = useState(-1)
  const escolhido = useRef<string | null>(null)

  useEffect(() => {
    // depois de escolher uma sugestão (ou ao digitar coordenada) não há o que buscar
    if (valor.trim().length < 2 || valor === escolhido.current || /^\s*-?\d/.test(valor)) {
      setSugestoes([])
      return
    }
    const ctl = new AbortController()
    const t = setTimeout(() => {
      buscarRuas(valor.trim(), ctl.signal)
        .then((r) => {
          setSugestoes(r)
          setAtivo(-1)
        })
        .catch(() => setSugestoes([]))
    }, 200)
    return () => {
      clearTimeout(t)
      ctl.abort()
    }
  }, [valor])

  const escolher = (s: string) => {
    escolhido.current = s
    onChange(s)
    setAberto(false)
    setAtivo(-1)
  }

  const aoTeclar = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!aberto || sugestoes.length === 0) return
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setAtivo((a) => (a + 1) % sugestoes.length)
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setAtivo((a) => (a <= 0 ? sugestoes.length - 1 : a - 1))
    } else if (e.key === 'Enter' && ativo >= 0) {
      e.preventDefault()
      escolher(sugestoes[ativo])
    } else if (e.key === 'Escape') {
      setAberto(false)
    }
  }

  const lista = aberto && sugestoes.length > 0
  return (
    <div className="campo">
      <label htmlFor={id}>{rotulo}</label>
      <input
        id={id}
        type="text"
        role="combobox"
        aria-expanded={lista}
        aria-controls={`${id}-lista`}
        aria-autocomplete="list"
        aria-activedescendant={ativo >= 0 ? `${id}-${ativo}` : undefined}
        autoComplete="off"
        spellCheck={false}
        maxLength={80}
        value={valor}
        placeholder={placeholder}
        onChange={(e) => {
          escolhido.current = null
          onChange(e.target.value)
          setAberto(true)
        }}
        onFocus={() => setAberto(true)}
        onBlur={() => setAberto(false)}
        onKeyDown={aoTeclar}
      />
      {lista && (
        <ul id={`${id}-lista`} role="listbox" className="campo__lista">
          {sugestoes.map((s, i) => (
            <li
              key={s}
              id={`${id}-${i}`}
              role="option"
              aria-selected={i === ativo}
              // mousedown (não click): o blur do input fecharia a lista antes do clique
              onMouseDown={(e) => {
                e.preventDefault()
                escolher(s)
              }}
            >
              {s}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
