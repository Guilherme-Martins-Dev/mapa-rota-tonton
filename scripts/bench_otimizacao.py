"""Benchmark da otimização do Yen (Lawler + A*) no grafo REAL de Messejana (cache em cache/).

Passos: (0) causa medida (tempos, nº de Dijkstras, vértices expandidos, cProfile) com o Yen original;
(1) cada candidata isolada (A = Lawler, B = A*, A+B); (2) verificação: custos de otimizar=True x False
nos mesmos pares e em 200 grafos aleatórios pequenos.

O trânsito é SIMULADO (v_atual = v_livre x fator em [0,5; 1,0] nas arestas TomTom); a TomTom NÃO é chamada.
Este script lê/grava o cache real; o pytest nunca deve fazer isso.

Uso: ./.venv/Scripts/python.exe scripts/bench_otimizacao.py [--saida docs/dados/bench-otimizacao.md]
"""
import argparse
import cProfile
import datetime
import io
import itertools
import math
import os
import platform
import pstats
import random
import statistics
import subprocess
import sys
import time
import types
from pathlib import Path

import networkx as nx
import osmnx as ox

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from tonton import rotas  # noqa: E402
from tonton.consumo import atribuir_consumo  # noqa: E402
from tonton.grafo import carregar_grafo  # noqa: E402
from tonton.pesos import atribuir_pesos, gravar_velocidades  # noqa: E402
from tonton.rotas import _haversine, _yen, heuristica_haversine, menor_rota, menores_rotas  # noqa: E402
from tonton.ruas import eh_tomtom  # noqa: E402

SEMENTE = 42
PESOS = ("length", "t_atual", "litros")
KS = (3, 5, 10)
PARES = 50
DIST_MIN_M = 2000
TOLERANCIA = 1e-9
# O "original" é o código de antes desta etapa (commit 7484526, rotas.py), lido do git e executado como módulo
# à parte; as demais variantes usam o código atual. D = pré-checagem barata do Dijkstra (sempre presente
# no código atual, inclusive com todas as flags desligadas); A = Lawler; B = A*.
COMMIT_ORIGINAL = "7484526"
# nome -> (lawler, astar, poda)   (C = poda de desvios, exige A*)
VARIANTES = {"original": (False, False, False), "D": (False, False, False), "A+D": (True, False, False),
             "B+D": (False, True, False), "A+B+D": (True, True, False), "A+B+C+D": (True, True, True)}
CANDIDATAS = tuple(v for v in VARIANTES if v != "original")


def carregar_original():
    fonte = subprocess.run(["git", "show", f"{COMMIT_ORIGINAL}:src/tonton/rotas.py"], capture_output=True,
                           check=True, cwd=Path(__file__).resolve().parents[1]).stdout.decode("utf-8")
    modulo = types.ModuleType("rotas_original")
    sys.modules["rotas_original"] = modulo  # o @dataclass precisa achar o módulo
    exec(compile(fonte, "rotas_original.py", "exec"), modulo.__dict__)
    return modulo


ORIGINAL = carregar_original()


def modulo_de(var):
    return ORIGINAL if var == "original" else rotas


def preparar_grafo():
    G = carregar_grafo()
    atribuir_pesos(G)  # sem TomTom: v_atual = v_livre
    rng = random.Random(SEMENTE)
    simuladas = 0
    for _, _, dados in G.edges(data=True):  # trânsito SIMULADO, só nas arestas que iriam à TomTom
        if eh_tomtom(dados):
            v_livre = dados["v_livre"]
            gravar_velocidades(dados, v_livre, v_livre * rng.uniform(0.5, 1.0))
            simuladas += 1
    atribuir_consumo(G)
    return G, simuladas


def sortear_pares(G):
    rng = random.Random(SEMENTE)
    nos = sorted(max(nx.strongly_connected_components(G), key=len))  # só onde há caminho nos dois sentidos
    pares = []
    while len(pares) < PARES:
        o, d = rng.sample(nos, 2)
        if _haversine(G.nodes[o]["y"], G.nodes[o]["x"], G.nodes[d]["y"], G.nodes[d]["x"]) > DIST_MIN_M:
            pares.append((o, d))
    return pares


def yen_k(G, o, d, k, peso, variante):
    if variante == "original":
        return list(itertools.islice(ORIGINAL._yen(G, o, d, peso), k))
    lawler, astar, poda = VARIANTES[variante]
    return list(itertools.islice(_yen(G, o, d, peso, lawler=lawler, astar=astar, poda_k=k if poda else None), k))


def cronometrar(f):
    t = time.perf_counter()
    r = f()
    return time.perf_counter() - t, r


def resumo(tempos_s):
    t = sorted(tempos_s)
    p90 = t[min(len(t) - 1, math.ceil(0.9 * len(t)) - 1)]
    return statistics.median(t) * 1000, p90 * 1000, t[-1] * 1000


def contar(G, f, modulo=rotas):
    """Executa f() contando chamadas a dijkstra e vértices expandidos (G.successors) POR FORA do código de produção."""
    estado = {"dijkstras": 0, "expandidos": 0}
    original_dij = modulo.dijkstra
    original_succ = G.successors

    def dij(*a, **kw):
        estado["dijkstras"] += 1
        return original_dij(*a, **kw)

    def succ(u):
        estado["expandidos"] += 1
        return original_succ(u)

    modulo.dijkstra, G.successors = dij, succ
    try:
        f()
    finally:
        modulo.dijkstra = original_dij
        del G.successors
    return estado["dijkstras"], estado["expandidos"]


def custos(rs):
    return [r.custo for r in rs]


def iguais(a, b):
    return len(a) == len(b) and all(abs(x - y) <= TOLERANCIA * max(1.0, abs(x)) for x, y in zip(a, b))


def grafo_aleatorio(rng):
    """Grafo pequeno com coordenadas; metade dos grafos tem length MENOR que a distância das coordenadas."""
    n = rng.randint(6, 12)
    G = nx.MultiDiGraph()
    for i in range(n):
        G.add_node(i, y=-3.83 + rng.uniform(0, 0.01), x=-38.49 + rng.uniform(0, 0.01))
    encolhe = rng.random() < 0.5
    for u in range(n):
        for v in range(n):
            if u == v or rng.random() > 0.35:
                continue
            for _ in range(rng.choice((1, 1, 1, 2))):
                reta = _haversine(G.nodes[u]["y"], G.nodes[u]["x"], G.nodes[v]["y"], G.nodes[v]["x"])
                comp = reta * (rng.uniform(0.3, 0.95) if encolhe else rng.uniform(1.0, 2.0))
                if rng.random() < 0.05:
                    comp = 0.0  # exercita o ramo de length ausente/zero
                vel = rng.uniform(5, 80)
                G.add_edge(u, v, length=comp, t_atual=comp / (vel / 3.6) if comp else rng.uniform(0, 5),
                           litros=comp / 1000 * rng.uniform(0.05, 0.2))
    return G, encolhe


def verificar_aleatorios(qtd=200):
    rng = random.Random(SEMENTE)
    comparados = diverg = sem_caminho = encolhidos = 0
    for _ in range(qtd):
        G, encolhe = grafo_aleatorio(rng)
        encolhidos += encolhe
        o, d = rng.sample(sorted(G.nodes), 2)
        for peso in PESOS:
            try:
                ref = list(itertools.islice(ORIGINAL._yen(G, o, d, peso), 6))
            except ORIGINAL.RotaInexistente:  # classe do módulo original, não a atual
                sem_caminho += 1
                continue
            for var in CANDIDATAS:
                comparados += 1
                if not iguais(custos(ref), custos(yen_k(G, o, d, 6, peso, var))):
                    diverg += 1
    return qtd, encolhidos, sem_caminho, comparados, diverg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", default=None)
    args = ap.parse_args()
    L = []

    def p(txt=""):
        print(txt, flush=True)
        L.append(txt)

    G, simuladas = preparar_grafo()
    pares = sortear_pares(G)
    p(f"Data {datetime.date.today()}; Python {platform.python_version()}, networkx {nx.__version__}, "
      f"osmnx {ox.__version__}; {platform.platform()}, {platform.processor()}, {os.cpu_count()} CPUs lógicas; semente {SEMENTE}.")
    p(f"Grafo REAL de Messejana (cache em disco, fonte `{G.graph.get('fonte', '?')}`): {G.number_of_nodes()} vértices, "
      f"{G.number_of_edges()} arestas. Trânsito SIMULADO (v_atual = v_livre x U[0,5; 1,0] em {simuladas} arestas "
      f"TomTom); a TomTom não foi chamada. {PARES} pares sorteados na maior componente fortemente conexa "
      f"({len(max(nx.strongly_connected_components(G), key=len))} vértices), distância em linha reta > {DIST_MIN_M} m.")
    p()

    # --- Passo 0: tempos do original ---
    p("## Passo 0: tempos (ms) por consulta, nos 50 pares (mediana / p90 / máx.), Yen original")
    p()
    p("| peso | menor_rota | Yen k=3 | Yen k=5 | Yen k=10 |")
    p("|---|---|---|---|---|")
    brutos = {}  # (peso, k, variante) -> lista de tempos por par
    base_dij = {}
    for peso in PESOS:
        brutos[(peso, 0, "original")] = [cronometrar(lambda: ORIGINAL.menor_rota(G, o, d, peso))[0] for o, d in pares]
        for k in KS:
            brutos[(peso, k, "original")] = [cronometrar(lambda: yen_k(G, o, d, k, peso, "original"))[0] for o, d in pares]
        cel = ["{:.1f} / {:.1f} / {:.1f}".format(*resumo(brutos[(peso, k, "original")])) for k in (0, *KS)]
        p(f"| {peso} | " + " | ".join(cel) + " |")
    p()

    # --- contagens ---
    p("## Passo 0: nº de Dijkstras e de vértices expandidos por consulta do Yen original (mediana / máx. nos 50 pares)")
    p()
    p("Expandido = vértice cujos sucessores foram percorridos (contado por um wrapper em `G.successors`, fora do código de produção).")
    p()
    p("| peso | k | Dijkstras | vértices expandidos | expandidos por Dijkstra |")
    p("|---|---|---|---|---|")
    for peso in PESOS:
        for k in KS:
            cont = [contar(G, lambda: yen_k(G, o, d, k, peso, "original"), ORIGINAL) for o, d in pares]
            dj, ex = [c[0] for c in cont], [c[1] for c in cont]
            por = [e / j for j, e in cont]
            p(f"| {peso} | {k} | {statistics.median(dj):.0f} / {max(dj)} | {statistics.median(ex):.0f} / {max(ex)} | "
              f"{statistics.median(por):.0f} |")
    p()
    # um Dijkstra simples: expandidos
    ex1 = [contar(G, lambda: ORIGINAL.menor_rota(G, o, d, "t_atual"), ORIGINAL)[1] for o, d in pares]
    p(f"Um `menor_rota` (t_atual) expande, em mediana, {statistics.median(ex1):.0f} dos {G.number_of_nodes()} vértices (máx. {max(ex1)}).")
    p()

    # --- profile ---
    mediana = statistics.median(brutos[("t_atual", 3, "original")])
    tipico = min(range(PARES), key=lambda i: abs(brutos[("t_atual", 3, "original")][i] - mediana))
    o, d = pares[tipico]
    pr = cProfile.Profile()
    pr.enable()
    yen_k(G, o, d, 3, "t_atual", "original")
    pr.disable()
    buf = io.StringIO()
    st = pstats.Stats(pr, stream=buf).sort_stats("tottime")
    st.print_stats(10)
    total = st.total_tt
    p("## Passo 0: cProfile de uma consulta típica (Yen original, k=3, t_atual, par de tempo mediano)")
    p()
    p(f"Tempo total sob o profile: {total * 1000:.0f} ms (o cProfile infla o tempo; vale a proporção). Ordenado por tempo próprio (tottime).")
    p()
    p("| função | chamadas | tempo próprio (ms) | % |")
    p("|---|---|---|---|")
    for (arq, lin, nome), (cc, nc, tt, ct, _) in sorted(st.stats.items(), key=lambda kv: -kv[1][2])[:8]:
        p(f"| `{Path(arq).name}:{nome}` | {nc} | {tt * 1000:.1f} | {100 * tt / total:.0f}% |")
    p()

    # --- candidatas ---
    p("## Passo 1: candidatas isoladas, tempo em ms por consulta (mediana / p90 / máx.) e speedup da mediana sobre o original")
    p()
    p("| peso | k | original | D | A+D | B+D | A+B+D | A+B+C+D |")
    p("|---|---|---|---|---|---|---|---|")
    lin_dj = []
    for peso in PESOS:
        brutos[(peso, 0, "D")] = [cronometrar(lambda: menor_rota(G, o, d, peso))[0] for o, d in pares]
        brutos[(peso, 0, "B A*")] = [cronometrar(lambda: menor_rota(G, o, d, peso, heuristica=heuristica_haversine(G, d, peso)))[0]
                                      for o, d in pares]
        for k in KS:
            for var in CANDIDATAS:
                brutos[(peso, k, var)] = [cronometrar(lambda: yen_k(G, o, d, k, peso, var))[0] for o, d in pares]
            base = statistics.median(brutos[(peso, k, "original")])
            base_d = statistics.median(brutos[(peso, k, "D")])
            cel = []
            for var in VARIANTES:
                m = resumo(brutos[(peso, k, var)])
                if var == "original":
                    extra = ""
                elif var == "D":
                    extra = f" ({base / (m[0] / 1000):.2f}x)"
                else:
                    extra = f" ({base / (m[0] / 1000):.2f}x; {base_d / (m[0] / 1000):.2f}x sobre D)"
                cel.append("{:.1f} / {:.1f} / {:.1f}".format(*m) + extra)
            p(f"| {peso} | {k} | " + " | ".join(cel) + " |")
    p()
    p("`menor_rota` (k=1), mediana / p90 / máx. em ms: Dijkstra original, Dijkstra atual (D) e A* (inclui montar a heurística, que varre as arestas):")
    p()
    p("| peso | original | D | A*+D |")
    p("|---|---|---|---|")
    for peso in PESOS:
        a, c, b = (resumo(brutos[(peso, 0, v)]) for v in ("original", "D", "B A*"))
        p(f"| {peso} | {a[0]:.1f} / {a[1]:.1f} / {a[2]:.1f} | {c[0]:.1f} / {c[1]:.1f} / {c[2]:.1f} ({a[0] / c[0]:.2f}x) | "
          f"{b[0]:.1f} / {b[1]:.1f} / {b[2]:.1f} ({a[0] / b[0]:.2f}x) |")
    p()
    t_h = [cronometrar(lambda: heuristica_haversine(G, pares[0][1], peso))[0] for peso in PESOS for _ in range(5)]
    p(f"Custo de montar a heurística (varredura O(E) + coordenadas), mediana de {len(t_h)} chamadas: {statistics.median(t_h) * 1000:.2f} ms.")
    p()
    p("Dijkstras e vértices expandidos por consulta (t_atual, mediana nos 50 pares):")
    p()
    p("| k | variante | Dijkstras | vértices expandidos |")
    p("|---|---|---|---|")
    for k in KS:
        for var in VARIANTES:
            cont = [contar(G, lambda: yen_k(G, o, d, k, "t_atual", var), modulo_de(var)) for o, d in pares]
            p(f"| {k} | {var} | {statistics.median(c[0] for c in cont):.0f} | {statistics.median(c[1] for c in cont):.0f} |")
    p()

    # --- verificação ---
    p("## Passo 2: verificação (custos das k rotas, tolerância 1e-9 relativa)")
    p()
    comp = {v: 0 for v in CANDIDATAS}
    div = {v: 0 for v in CANDIDATAS}
    for peso in PESOS:
        for k in KS:
            for (o, d) in pares:
                ref = custos(yen_k(G, o, d, k, peso, "original"))
                for var in CANDIDATAS:
                    comp[var] += 1
                    if not iguais(ref, custos(yen_k(G, o, d, k, peso, var))):
                        div[var] += 1
                        p(f"DIVERGÊNCIA {var} {peso} k={k} par {(o, d)}")
    # API pública: menores_rotas(otimizar=True) x (otimizar=False)
    api_comp = api_div = 0
    for peso in PESOS:
        for (o, d) in pares:
            api_comp += 1
            if not iguais(custos(list(itertools.islice(ORIGINAL._yen(G, o, d, peso), 5))),
                          custos(menores_rotas(G, o, d, 5, peso, otimizar=True))):
                api_div += 1
    p("| variante | comparações (par x peso x k) | divergências |")
    p("|---|---|---|")
    for var in CANDIDATAS:
        p(f"| {var} | {comp[var]} | {div[var]} |")
    p()
    p(f"API pública `menores_rotas(k=5)`, otimizar=True x False: {api_comp} comparações (par x peso), {api_div} divergências.")
    p()
    qtd, enc, sem, cmp_, dv = verificar_aleatorios()
    p(f"Grafos aleatórios pequenos (6 a 12 vértices, com coordenadas, paralelas e 5% de arestas com length 0): {qtd} grafos, "
      f"{enc} com `length` MENOR que a distância das coordenadas; {sem} (grafo, peso) sem caminho (nada a comparar); "
      f"{cmp_} comparações (grafo x peso x variante, k=6): {dv} divergências.")
    p()
    if args.saida:
        Path(args.saida).write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
