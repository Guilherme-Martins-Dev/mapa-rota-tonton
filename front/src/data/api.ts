import { ehRotas, type Rotas } from './tipos'

/** Cliente da API (`src/tonton/api.py`). Em dev o Vite faz proxy de /api para o uvicorn na porta 8000. */
export interface Veiculo {
  id: string
  nome: string
  combustivel: string
  consumo_urbano_l100: number
  consumo_estrada_l100: number
  origem: string
}

export interface Metadados {
  origem: { entrada: string; lat: number; lon: number }
  destino: { entrada: string; lat: number; lon: number }
  veiculo: string
  transito: 'simulado'
}

export type RotasDaApi = Rotas & { metadados: Metadados }

/** Erro com a mensagem em português que a API devolve em `detail` (422/404). */
export class ErroApi extends Error {
  readonly status: number
  constructor(mensagem: string, status: number) {
    super(mensagem)
    this.status = status
  }
}

async function pegar<T>(caminho: string, params: Record<string, string>, signal?: AbortSignal): Promise<T> {
  const url = `${caminho}?${new URLSearchParams(params)}`
  let r: Response
  try {
    r = await fetch(url, { signal })
  } catch (e) {
    if ((e as Error).name === 'AbortError') throw e
    throw new ErroApi('Não foi possível falar com o servidor de rotas. Ele está rodando?', 0)
  }
  if (!r.ok) {
    let detalhe = `Erro ${r.status} no servidor.`
    try {
      const corpo = (await r.json()) as { detail?: unknown }
      if (typeof corpo.detail === 'string') detalhe = corpo.detail
      else if (r.status === 422) detalhe = 'Preencha origem e destino (mínimo de 2 caracteres).'
    } catch {
      /* corpo que não é JSON: fica a mensagem genérica */
    }
    throw new ErroApi(detalhe, r.status)
  }
  return (await r.json()) as T
}

export const buscarVeiculos = (signal?: AbortSignal) => pegar<Veiculo[]>('/api/veiculos', {}, signal)

export const buscarRuas = (q: string, signal?: AbortSignal) => pegar<string[]>('/api/ruas', { q }, signal)

export async function buscarRotas(
  origem: string,
  destino: string,
  veiculo: string,
  signal?: AbortSignal,
): Promise<RotasDaApi> {
  const json = await pegar<RotasDaApi>('/api/rotas', { origem, destino, veiculo }, signal)
  if (!ehRotas(json) || !json.metadados) throw new ErroApi('Resposta do servidor fora do formato esperado.', 0)
  return json
}
