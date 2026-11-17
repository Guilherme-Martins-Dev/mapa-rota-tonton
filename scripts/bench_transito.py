"""Benchmark da atualização incremental do trânsito. Fora do CI.

(a) GRAFO SINTÉTICO do porte de Messejana (~750 nós, ~1900 arestas, ~230 TomTom): tempo do
    recálculo completo (pesos + consumo) contra o incremental com 5%, 20% e 100% dos pontos
    alterados; tempo de menor_rota; tempo de rota_continua_otima (e conferência contra o Dijkstra).
    `consultar` é falso e instantâneo: isola o custo de CPU.
(b) LATÊNCIA REAL da TomTom: 8 pontos de Messejana em sequência, sem cache. A chave vem só de
    tonton.config.tomtom_key(); nunca é impressa, e erros mostram só o status HTTP / o tipo da exceção.

Uso: ./.venv/Scripts/python.exe scripts/bench_transito.py [--saida docs/dados/bench-transito.md] [--sem-rede]
"""
import argparse
import copy
import datetime
import platform
import random
import statistics
import sys
import time
from pathlib import Path

import networkx as nx
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from tonton import transito  # noqa: E402
from tonton.atualizacao import atualizar_transito, indexar, rota_continua_otima  # noqa: E402
from tonton.consumo import atribuir_consumo  # noqa: E402
from tonton.pesos import atribuir_pesos  # noqa: E402
from tonton.rotas import RotaInexistente, menor_rota  # noqa: E402

SEMENTE = 42
LINHAS, COLUNAS = 27, 28   # 756 nós
N_TOMTOM = 230
PONTOS_REAIS = [(-3.8267, -38.4935), (-3.8240, -38.4900), (-3.8210, -38.4870), (-3.8180, -38.4840),
                (-3.8140, -38.4810), (-3.8100, -38.4780), (-3.8050, -38.4740), (-3.8000, -38.4700)]
PONTOS_MESSEJANA = 211  # pontos médios distintos medidos em Messejana (docs/dados/fumaca-real-messejana.md)


def grafo_sintetico(semente: int = SEMENTE) -> nx.MultiDiGraph:
    """Grade 27x28 em torno de Messejana; cada rua é mão dupla (30%) ou mão única; ~230 arestas TomTom."""
    rng = random.Random(semente)
    G = nx.MultiDiGraph()
    for i in range(LINHAS):
        for j in range(COLUNAS):
            G.add_node((i, j), y=-3.84 + i * 0.0008, x=-38.50 + j * 0.0008)
    pares = []
    for i in range(LINHAS):
        for j in range(COLUNAS):
            if j + 1 < COLUNAS:
                pares.append(((i, j), (i, j + 1)))
            if i + 1 < LINHAS:
                pares.append(((i, j), (i + 1, j)))
    arestas = []
    for a, b in pares:
        if rng.random() < 0.3:
            arestas += [(a, b), (b, a)]
        else:
            arestas.append((a, b) if rng.random() < 0.5 else (b, a))
    tomtom = set(rng.sample(range(len(arestas)), N_TOMTOM))
    for k, (u, v) in enumerate(arestas):
        G.add_edge(u, v, length=rng.uniform(50, 150),
                   highway="secondary" if k in tomtom else "residential")
    return G


def consultar_falso(mudar: set | None = None):
    """consultar(lat, lon) instantâneo e determinístico por ponto; os de `mudar` recebem outro v_atual."""
    def consultar(lat, lon):
        rng = random.Random(f"{SEMENTE}:{lat!r}:{lon!r}")
        livre = rng.uniform(30, 70)
        atual = livre * rng.uniform(0.3, 1.0)
        desloc = rng.choice((-1, 1)) * rng.uniform(5, 15)
        if mudar is not None and (lat, lon) in mudar:
            atual = max(5.0, atual + desloc)
        return {"freeFlowSpeed": livre, "currentSpeed": atual}
    return consultar


def mediana_ms(f, repeticoes: int, preparar=None) -> float:
    tempos = []
    for _ in range(repeticoes):
        arg = preparar() if preparar else None
        t0 = time.perf_counter()
        f(arg) if preparar else f()
        tempos.append((time.perf_counter() - t0) * 1000)
    return statistics.median(tempos)


def bench_cpu(linhas: list[str]) -> None:
    G0 = grafo_sintetico()
    n_pontos = len(indexar(G0).arestas_por_ponto)
    linhas += [
        "## (a) CPU em grafo SINTÉTICO (não é Messejana)", "",
        f"Grafo sintético: {G0.number_of_nodes()} nós, {G0.number_of_edges()} arestas, "
        f"{sum(len(v) for v in indexar(G0).arestas_por_ponto.values())} arestas TomTom em "
        f"{n_pontos} pontos médios distintos. `consultar` falso e instantâneo (só CPU). "
        "Mediana de 30 execuções (recálculo/incremental) ou 20 (menor_rota); a cópia do grafo fica fora da medição.", "",
    ]

    # estado inicial: grafo já com pesos de um refresh completo
    cons0 = consultar_falso()
    atribuir_pesos(G0, cons0)
    atribuir_consumo(G0)

    completo = mediana_ms(lambda G: (atribuir_pesos(G, cons0), atribuir_consumo(G)), 30, lambda: copy.deepcopy(G0))
    linhas += ["| operação | tempo (ms) |", "|---|---|", f"| recálculo COMPLETO (pesos + consumo, todas as arestas) | {completo:.2f} |"]

    pontos = list(indexar(G0).arestas_por_ponto)
    for frac in (0.05, 0.20, 1.00):
        rng = random.Random(SEMENTE + 1)
        mudar = set(rng.sample(pontos, max(1, round(frac * len(pontos)))))
        fixo = consultar_falso(mudar)

        def preparar():
            G = copy.deepcopy(G0)
            return G, indexar(G)

        t = mediana_ms(lambda a: atualizar_transito(a[0], a[1], fixo), 30, preparar)
        G, ind = preparar()
        r = atualizar_transito(G, ind, fixo)
        linhas.append(f"| incremental, {frac:.0%} dos pontos alterados ({len(r.alteradas)} arestas reescritas) | {t:.2f} |")
    linhas.append("")

    # Dijkstra e rota_continua_otima
    nos = list(G0.nodes)
    rng = random.Random(SEMENTE)
    pares = []
    while len(pares) < 20:
        o, d = rng.sample(nos, 2)
        if nx.has_path(G0, o, d):
            pares.append((o, d))
    t_dij = statistics.median(
        mediana_ms(lambda o=o, d=d: menor_rota(G0, o, d, "t_atual"), 5) for o, d in pares)
    rota_ex = menor_rota(G0, *pares[0], "t_atual")
    G, ind = copy.deepcopy(G0), None
    ind = indexar(G)
    rng = random.Random(SEMENTE + 1)
    mudar = set(rng.sample(pontos, max(1, round(0.05 * len(pontos)))))
    res = atualizar_transito(G, ind, consultar_falso(mudar))
    t_cont = mediana_ms(lambda: rota_continua_otima(G, rota_ex, res, "t_atual"), 200)
    linhas += [
        f"- `menor_rota` (t_atual), mediana entre 20 pares origem-destino alcançáveis (cada um: mediana de 5): {t_dij:.2f} ms.",
        f"- `rota_continua_otima` (resultado de 5% alterados, rota de {len(rota_ex.arestas)} arestas): {t_cont * 1000:.1f} us (mediana de 200).",
        "",
    ]

    # Conferência: quando diz True, o Dijkstra confirma o mesmo custo?
    linhas += [
        "### Conferência de `rota_continua_otima` contra o Dijkstra", "",
        "100 pares origem-destino alcançáveis por linha; em cada um, variação aleatória (pioram e melhoram) de uma fração dos pontos. "
        "`True` = a função diz que a rota segue ótima; `custo igual` = entre os `True`, o Dijkstra refeito deu o mesmo custo de "
        "uma rota (a rota antiga, reavaliada, custa o mesmo que a nova ótima, tolerância 1e-9). Esperado: sempre igual.", "",
        "| peso | pontos alterados | True | False | True com custo igual (Dijkstra) |", "|---|---|---|---|---|",
    ]
    for peso in ("t_atual", "litros"):
        for frac in (0.01, 0.05, 0.20):
            verd = fals = ok = 0
            rng = random.Random(SEMENTE + 7)
            tentativas = 0
            while tentativas < 100:
                o, d = rng.sample(nos, 2)
                if not nx.has_path(G0, o, d):
                    continue
                tentativas += 1
                G = copy.deepcopy(G0)
                rota = menor_rota(G, o, d, peso)
                mudar = set(rng.sample(pontos, max(1, round(frac * len(pontos)))))
                res = atualizar_transito(G, indexar(G), consultar_falso(mudar))
                if rota_continua_otima(G, rota, res, peso):
                    verd += 1
                    custo_antiga = sum(min(x[peso] for x in G[u][v].values()) for u, v, _ in rota.arestas)
                    if abs(menor_rota(G, o, d, peso).custo - custo_antiga) <= 1e-9:
                        ok += 1
                else:
                    fals += 1
            linhas.append(f"| {peso} | {frac:.0%} | {verd} | {fals} | {ok} |")
    linhas.append("")


def bench_rede(linhas: list[str]) -> None:
    linhas += ["## (b) Latência REAL da TomTom", ""]
    tempos, status = [], []
    for lat, lon in PONTOS_REAIS:
        t0 = time.perf_counter()
        try:
            transito.consultar_trafego(lat, lon)
            tempos.append((time.perf_counter() - t0) * 1000)
            status.append("ok")
        except requests.HTTPError as e:
            status.append(f"HTTP {e.response.status_code}")  # nunca imprimir a URL
        except Exception as e:
            status.append(type(e).__name__)  # só o tipo: a mensagem pode conter a URL
    linhas.append(f"{len(PONTOS_REAIS)} pontos de Messejana em sequência, sem cache, `transito.consultar_trafego`. Resultados: {', '.join(status)}.")
    linhas.append("")
    if not tempos:
        linhas += ["Nenhuma consulta funcionou: **latência não medida**; nada foi extrapolado.", ""]
        return
    med, mn, mx = statistics.median(tempos), min(tempos), max(tempos)
    linhas += [
        "| consultas ok | mediana (ms) | mín (ms) | máx (ms) |", "|---|---|---|---|",
        f"| {len(tempos)} | {med:.0f} | {mn:.0f} | {mx:.0f} |", "",
        f"**EXTRAPOLAÇÃO** (não medida): refresh completo sequencial de {PONTOS_MESSEJANA} pontos = {PONTOS_MESSEJANA} x mediana "
        f"= {PONTOS_MESSEJANA * med / 1000:.0f} s (faixa {PONTOS_MESSEJANA * mn / 1000:.0f} a {PONTOS_MESSEJANA * mx / 1000:.0f} s). "
        "Supõe latência constante, sem limite de taxa nem falhas, e que 8 pontos representam os 211.", "",
    ]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", default=None)
    ap.add_argument("--sem-rede", action="store_true")
    args = ap.parse_args()
    linhas = [
        "# Benchmark do trânsito incremental", "",
        f"Medido com `scripts/bench_transito.py` em {datetime.date.today().isoformat()}. "
        f"Python {platform.python_version()}, networkx {nx.__version__}, requests {requests.__version__}, "
        f"{platform.system()} {platform.release()}, {platform.processor() or platform.machine()}; semente {SEMENTE}. "
        "Uma máquina, uma sessão: ordem de grandeza, não garantia.", "",
    ]
    bench_cpu(linhas)
    if not args.sem_rede:
        bench_rede(linhas)
    texto = "\n".join(linhas) + "\n"
    print(texto)
    if args.saida:
        Path(args.saida).write_text(texto, encoding="utf-8")


if __name__ == "__main__":
    main()
