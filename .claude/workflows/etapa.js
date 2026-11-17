export const meta = {
  name: 'etapa',
  description: 'Executa UMA etapa (1-5) do back-end de rotas: desenho, código, testes, revisão e PR',
  whenToUse: 'Com args {"etapa": N}. Parte da main atualizada, abre o PR da etapa e para (o merge é do usuário).',
  phases: [
    { title: 'Preparar', detail: 'branch da etapa a partir da main atualizada' },
    { title: 'Desenho', detail: 'arquiteto-grafos' },
    { title: 'Implementar', detail: 'implementador' },
    { title: 'Testar', detail: 'testador (pytest verde)' },
    { title: 'Revisar', detail: 'revisor, até 2 voltas de correção' },
    { title: 'Publicar', detail: 'commit, push e PR' },
  ],
}

const ETAPAS = {
  1: {
    slug: 'identificar-ruas',
    titulo: 'Identificar ruas',
    escopo: `Parte 1 do analisar.md. Em src/tonton/ruas.py (e ajustes em grafo.py): para cada aresta do grafo devolver nome da rua
(o campo name pode ser str, lista ou ausente), trecho (u -> v), PONTO MÉDIO da geometria da aresta (lat, lon) e o cruzamento seguinte (v),
pois o trajeto começa a partir da próxima aresta/cruzamento. Filtro por highway em {trunk, primary, secondary, tertiary}
(highway também pode ser lista). Busca de rua por nome com normalização de acentos e caixa; migrar a ideia de tem_nome do antigo api.py.`,
  },
  2: {
    slug: 'tempo',
    titulo: 'Pesos de tempo (t_livre, t_atual)',
    escopo: `Parte 2 do analisar.md. Estender src/tonton/transito.py: consulta TomTom no ponto médio de cada trecho filtrado (etapa 1),
cache em disco em cache/ com validade, deduplicação de consultas pelo mesmo segmento, fallback para maxspeed/velocidade padrão por tipo de via
quando a rede ou a cota falhar. Criar src/tonton/pesos.py: t_livre e t_atual em segundos = comprimento (m) / velocidade (m/s), gravados nas arestas.
ATENÇÃO: o analisar.md diz velocidade/espaço, mas o certo (quadro) é comprimento/velocidade; registrar isso na descrição do PR.`,
  },
  3: {
    slug: 'guloso-menor-tempo',
    titulo: 'Dijkstra: menor tempo',
    escopo: `Parte 3 do analisar.md. src/tonton/rotas.py: Dijkstra escrito à mão (heapq) com relaxamento (se d[u]+w(u,v) < d[v] então d[v]=d[u]+w(u,v)),
parametrizado pelo nome do atributo de peso (t_atual, t_livre, length). Reconstrói o caminho por predecessores; em arestas paralelas (MultiDiGraph) usa a de menor peso;
destino inalcançável levanta erro claro. Não enumerar todas as trajetórias. Teste com o grafo do quadro (d=38 vs 39) e comparação com networkx.shortest_path em grafo sintético.`,
  },
  4: {
    slug: 'consumo',
    titulo: 'Menor consumo de combustível',
    escopo: `Parte 4 do analisar.md. src/tonton/consumo.py: litros = comprimento_km x f(v)/100, com f(v) em L/100km em formato de U
(alto em baixa velocidade, mínimo por volta de 60-70 km/h, sobe em alta), parâmetros por veículo configuráveis em config.py. Usa a velocidade atual (t_atual).
Grava o peso 'litros' nas arestas e reaproveita o Dijkstra de rotas.py com esse peso. Sem velocidade válida (<=0) usar a mais baixa da curva.`,
  },
  5: {
    slug: 'planejador',
    titulo: 'Planejador completo',
    escopo: `Parte 5 do analisar.md. src/tonton/planejador.py e src/tonton/cli.py (python -m tonton): dado origem e destino (lat,lon ou nome de rua,
ligados ao cruzamento mais próximo com ox.distance.nearest_nodes), calcula as 3 rotas (menor distância = length, menor tempo = t_atual, menor consumo = litros)
e imprime comparação (km, min, L). Exporta GeoJSON da rota (contrato para o futuro front) e plot simples com ox.plot_graph_route (opção --mostrar).
Atualizar o README com o uso.`,
  },
}

const etapa = args && args.etapa
const E = ETAPAS[etapa]
if (!E) throw new Error('Passe args {"etapa": 1..5}')
const branch = `etapa/${etapa}-${E.slug}`
const PY = './.venv/Scripts/python.exe'

// Os agentes de .claude/agents/ só são registrados no início da sessão; para funcionar sempre,
// cada papel roda como general-purpose e lê a própria definição no arquivo.
const como = (nome, tarefa, opts) =>
  agent(
    `Você atua como o agente "${nome}". Leia primeiro .claude/agents/${nome}.md (ignore o frontmatter) e siga essas instruções à risca. Leia também as skills listadas em "skills:" no frontmatter dele (.claude/skills/<nome>/SKILL.md).

${tarefa}`,
    { ...opts, agentType: 'general-purpose' },
  )

const TESTE = {
  type: 'object',
  properties: {
    passou: { type: 'boolean' },
    resumo: { type: 'string' },
    falhas: { type: 'array', items: { type: 'string' } },
  },
  required: ['passou', 'resumo'],
}
const REVISAO = {
  type: 'object',
  properties: {
    aprovado: { type: 'boolean' },
    problemas: { type: 'array', items: { type: 'string' } },
  },
  required: ['aprovado'],
}

phase('Preparar')
await agent(
  `No repositório atual: git checkout main && git pull --ff-only && git checkout -b ${branch}. ` +
    `Se a branch já existir, apenas faça checkout nela. Confirme com git branch --show-current e devolva só o nome.`,
  { label: 'branch', phase: 'Preparar', effort: 'low' },
)

phase('Desenho')
const desenho = await como(
  'arquiteto-grafos',
  `Etapa ${etapa} - ${E.titulo}.\n\nEscopo:\n${E.escopo}\n\nProduza o desenho e os critérios de aceite.`,
  { label: 'arquiteto', phase: 'Desenho' },
)

phase('Implementar')
await como(
  'implementador',
  `Etapa ${etapa} - ${E.titulo}. Implemente conforme o desenho abaixo (estamos na branch ${branch}).\n\nEscopo:\n${E.escopo}\n\nDesenho:\n${desenho}`,
  { label: 'implementador', phase: 'Implementar' },
)

const testar = (rotulo) =>
  como(
    'testador',
    `Etapa ${etapa} - ${E.titulo}. Escreva (ou atualize) os testes da etapa e rode ${PY} -m pytest -q. ` +
      `Critérios de aceite do desenho:\n${desenho}`,
    { label: rotulo, phase: 'Testar', schema: TESTE },
  )

phase('Testar')
let teste = await testar('testador')
for (let i = 0; i < 2 && !teste.passou; i++) {
  await como(
    'implementador',
    `Os testes da etapa ${etapa} falharam. Corrija o CÓDIGO em src/tonton/ (não afrouxe os testes sem motivo):\n${teste.resumo}\n${(teste.falhas || []).join('\n')}`,
    { label: `corrigir-teste-${i + 1}`, phase: 'Testar' },
  )
  teste = await testar(`testador-${i + 2}`)
}
if (!teste.passou) {
  log('Testes ainda falhando após as correções; não vou abrir PR.')
  return { etapa, branch, pr: null, motivo: 'testes falhando', teste }
}

phase('Revisar')
let revisao = await como('revisor', `Revise a etapa ${etapa} - ${E.titulo} na branch ${branch}.`, {
  label: 'revisor',
  phase: 'Revisar',
  schema: REVISAO,
})
for (let i = 0; i < 2 && !revisao.aprovado; i++) {
  await como(
    'implementador',
    `O revisor reprovou a etapa ${etapa}. Corrija:\n${(revisao.problemas || []).join('\n')}`,
    { label: `corrigir-revisao-${i + 1}`, phase: 'Revisar' },
  )
  teste = await testar(`testador-rev-${i + 1}`)
  if (!teste.passou) break
  revisao = await como('revisor', `Revise de novo a etapa ${etapa} na branch ${branch}.`, {
    label: `revisor-${i + 2}`,
    phase: 'Revisar',
    schema: REVISAO,
  })
}
if (!teste.passou || !revisao.aprovado) {
  log('Revisão não aprovada ou testes quebrados; não vou abrir PR.')
  return { etapa, branch, pr: null, motivo: 'reprovado', teste, revisao }
}

phase('Publicar')
const pr = await agent(
  `Publique a etapa ${etapa} (${E.titulo}) na branch ${branch}:\n` +
    `1. git status; confirme que não há .env, cache/ nem chaves no que será commitado (o repo é público).\n` +
    `2. git add dos arquivos da etapa e git commit com mensagem "Etapa ${etapa}: ${E.titulo}" terminando com a linha\n` +
    `   Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n` +
    `3. siga a skill fluxo-pr (.claude/skills/fluxo-pr/SKILL.md): push com GIT_TERMINAL_PROMPT=0 e o gh como credential helper; se passar de 1 minuto, cancele e avise\n` +
    `4. gh pr create --base main --title "Etapa ${etapa}: ${E.titulo}" com corpo em português: o que foi feito, como testar (${PY} -m pytest), ` +
    `decisões/ajustes em relação ao quadro e ao analisar.md, terminando com a linha\n   🤖 Generated with [Claude Code](https://claude.com/claude-code)\n` +
    `NÃO faça merge. Devolva só a URL do PR.`,
  { label: 'publicar', phase: 'Publicar', effort: 'low' },
)

return { etapa, branch, pr, teste: teste.resumo }
