"""Benchmark das rotas alternativas em GRAFO SINTÉTICO (grade n x n). Não é Messejana.

Mede: tempo de menor_rota vs menores_rotas (Yen) com k = 3, 5, 10; sobreposição da 2ª rota de
Yen com a ótima; quantos candidatos de Yen foram precisos para achar k alternativas distintas.
Também confere o Yen contra um oráculo (força bruta) em grafos pequenos.

Uso: ./.venv/Scripts/python.exe scripts/bench_alternativas.py [--saida docs/dados/bench-alternativas.md]
"""
import argparse
import itertools
import platform
import random
import statistics
import sys
import time
from pathlib import Path

import networkx as nx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from tonton.rotas import _sobreposicao, _yen, menor_rota, menores_rotas, rotas_alternativas  # noqa: E402

SEMENTE = 42
PESO = "t_atual"


def grade(n: int, semente: int = SEMENTE) -> nx.MultiDiGraph:
    """Grade n x n, ruas de mão dupla; length em [50, 150] m e velocidade em [20, 60] km/h aleatórios."""
    rng = random.Random(semente)
    G = nx.MultiDiGraph()
    for i, j in itertools.product(range(n), repeat=2):
        G.add_node((i, j))
    for i, j in itertools.product(range(n), repeat=2):
        for di, dj in ((1, 0), (0, 1)):
            a, b = (i, j), (i + di, j + dj)
            if b not in G:
                continue
            for u, v in ((a, b), (b, a)):
                comp = rng.uniform(50, 150)
                G.add_edge(u, v, length=comp, t_atual=comp / (rng.uniform(20, 60) / 3.6))
    return G


def tempo(f, repeticoes: int) -> float:
    """Mediana, em segundos, de `repeticoes` execuções."""
    amostras = []
    for _ in range(repeticoes):
        t0 = time.perf_counter()
        f()
        amostras.append(time.perf_counter() - t0)
    return statistics.median(amostras)


def sobreposicao(G, a, b) -> float:
    """Fração do comprimento de b que usa arestas de a."""
    total = sum(G[u][v][k]["length"] for u, v, k in b.arestas)
    comum = sum(G[u][v][k]["length"] for u, v, k in b.arestas if (u, v, k) in set(a.arestas))
    return comum / total


def candidatos_necessarios(G, o, d, k, max_sobreposicao, limite=100):
    """Uma passada por _yen, com o mesmo critério de rotas_alternativas: (candidatos gerados, aceitas, segundos).

    Para ao achar k rotas distintas ou ao gerar `limite` candidatos.
    """
    t0 = time.perf_counter()
    aceitas, usadas, gerados = [], [], 0
    for cand in itertools.islice(_yen(G, o, d, PESO), limite):
        gerados += 1
        if aceitas and _sobreposicao(G, cand, usadas) > max_sobreposicao:
            continue
        aceitas.append(cand)
        usadas.append(set(cand.arestas))
        if len(aceitas) == k:
            break
    return gerados, len(aceitas), time.perf_counter() - t0


def oraculo(semente: int):
    """Yen == força bruta (todos os caminhos simples) num grafo pequeno com pesos aleatórios.

    Devolve None se o grafo sorteado não tem caminho de 0 a n-1 (nada a comparar); senão True/False.
    """
    rng = random.Random(semente)
    G = nx.MultiDiGraph()
    n = 7
    for u, v in itertools.permutations(range(n), 2):
        if rng.random() < 0.45:
            for _ in range(rng.choice((1, 1, 2))):  # às vezes aresta paralela
                G.add_edge(u, v, t_atual=rng.uniform(1, 10))
    if 0 not in G or n - 1 not in G or not nx.has_path(G, 0, n - 1):
        return None  # caso sem rota: nada a comparar
    todos = []
    for caminho in nx.all_simple_paths(nx.DiGraph(G), 0, n - 1):
        custo = sum(min(d["t_atual"] for d in G[u][v].values()) for u, v in zip(caminho, caminho[1:]))
        todos.append(custo)
    todos.sort()
    yen = [r.custo for r in menores_rotas(G, 0, n - 1, k=len(todos) + 3, peso=PESO)]
    return len(yen) == len(todos) and all(abs(a - b) < 1e-9 for a, b in zip(yen, todos))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--saida", default=None, help="arquivo .md para gravar o resultado")
    args = p.parse_args()
    linhas = []

    def reg(texto=""):
        print(texto)
        linhas.append(texto)

    reg(f"Python {platform.python_version()}, networkx {nx.__version__}, {platform.system()} {platform.release()}; "
        f"semente {SEMENTE}; peso `{PESO}`.")
    reg()
    resultados = [oraculo(s) for s in range(200)]
    comparados = [r for r in resultados if r is not None]
    ok = sum(comparados)
    reg(f"Oráculo (força bruta, 7 vértices, paralelas, 200 sementes): {len(resultados) - len(comparados)} grafos "
        f"sem caminho de 0 a 6 (nada a comparar); Yen igual à força bruta em {ok}/{len(comparados)} grafos com caminho.")
    reg()
    reg("| grade | vértices | arestas | menor_rota (ms) | Yen k=3 (ms) | Yen k=5 (ms) | Yen k=10 (ms) |")
    reg("|---|---|---|---|---|---|---|")
    dados_cand = []
    for n in (30, 60):
        G = grade(n)
        o, d = (0, 0), (n - 1, n - 1)
        t_base = tempo(lambda: menor_rota(G, o, d, PESO), 5)
        tk = {k: tempo(lambda k=k: menores_rotas(G, o, d, k, PESO), 3) for k in (3, 5, 10)}
        reg(f"| {n}x{n} | {G.number_of_nodes()} | {G.number_of_edges()} | {t_base * 1e3:.1f} | "
            f"{tk[3] * 1e3:.0f} | {tk[5] * 1e3:.0f} | {tk[10] * 1e3:.0f} |")
        rotas = menores_rotas(G, o, d, 3, PESO)
        dados_cand.append((n, G, o, d, rotas))
    reg()
    reg("Tempos: mediana de 5 execuções (menor_rota) ou 3 (Yen); origem e destino em cantos opostos.")
    reg()
    reg("| grade | custo ótima (s) | custo 2ª Yen (s) | sobreposição 2ª x ótima | custo 3ª Yen (s) | sobreposição 3ª x ótima |")
    reg("|---|---|---|---|---|---|")
    for n, G, o, d, r in dados_cand:
        reg(f"| {n}x{n} | {r[0].custo:.1f} | {r[1].custo:.1f} | {sobreposicao(G, r[0], r[1]):.1%} | "
            f"{r[2].custo:.1f} | {sobreposicao(G, r[0], r[2]):.1%} |")
    reg()
    reg("Candidatos de Yen gerados até achar k rotas distintas (limite de 100; 'não achou' = só "
        "`aceitas` rotas em 100 candidatos). Uma execução cronometrada por linha.")
    reg()
    reg("| grade | k | max_sobreposicao | candidatos gerados | rotas aceitas | tempo (s) |")
    reg("|---|---|---|---|---|---|")
    for n, G, o, d, _ in dados_cand:
        for k, ms in ((3, 0.8), (5, 0.8), (3, 0.5)):
            c, a, t = candidatos_necessarios(G, o, d, k, ms)
            reg(f"| {n}x{n} | {k} | {ms} | {c} | {a}{'' if a == k else ' (não achou)'} | {t:.2f} |")
    if args.saida:
        Path(args.saida).write_text("\n".join(linhas) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
