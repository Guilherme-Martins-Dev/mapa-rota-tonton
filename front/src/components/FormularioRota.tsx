import { useEffect, useState } from 'react'
import { buscarVeiculos, type Veiculo } from '../data/api'
import { Botao } from '../ui'
import { CampoRua } from './CampoRua'
import './formulario.css'

export type Pedido = { origem: string; destino: string; veiculo: string }
type Props = { carregando: boolean; erro: string | null; onBuscar: (p: Pedido) => void }

/** Origem, destino e veículo. A busca só dispara no envio (Enter ou botão), nunca a cada tecla. */
export function FormularioRota({ carregando, erro, onBuscar }: Props) {
  const [origem, setOrigem] = useState('')
  const [destino, setDestino] = useState('')
  const [veiculo, setVeiculo] = useState('popular')
  const [veiculos, setVeiculos] = useState<Veiculo[]>([])

  useEffect(() => {
    const ctl = new AbortController()
    buscarVeiculos(ctl.signal)
      .then(setVeiculos)
      .catch(() => setVeiculos([])) // sem API o seletor fica só com o padrão
    return () => ctl.abort()
  }, [])

  const completo = origem.trim().length >= 2 && destino.trim().length >= 2
  const atual = veiculos.find((v) => v.id === veiculo)

  return (
    <form
      className="formulario"
      onSubmit={(e) => {
        e.preventDefault()
        if (completo && !carregando) onBuscar({ origem: origem.trim(), destino: destino.trim(), veiculo })
      }}
    >
      <CampoRua rotulo="De onde" valor={origem} onChange={setOrigem} placeholder="Rua ou lat,lon" />
      <CampoRua rotulo="Para onde" valor={destino} onChange={setDestino} placeholder="Rua ou lat,lon" />
      <div className="formulario__linha">
      <div className="campo">
        <label htmlFor="veiculo">Veículo</label>
        <select id="veiculo" value={veiculo} onChange={(e) => setVeiculo(e.target.value)}>
          {veiculos.length === 0 && <option value="popular">Compacto popular</option>}
          {veiculos.map((v) => (
            <option key={v.id} value={v.id}>
              {v.nome}
            </option>
          ))}
        </select>
      </div>
      <Botao type="submit" disabled={!completo || carregando} aria-busy={carregando}>
        {carregando ? 'Calculando' : 'Traçar rotas'}
      </Botao>
      </div>
      {atual && (
        <p className="formulario__dica">
          {atual.combustivel}, {atual.consumo_urbano_l100.toString().replace('.', ',')} L/100 km na cidade e{' '}
          {atual.consumo_estrada_l100.toString().replace('.', ',')} na estrada. Fonte: {atual.origem}.
        </p>
      )}
      {erro && (
        <p role="alert" className="formulario__erro">
          {erro}
        </p>
      )}
    </form>
  )
}
