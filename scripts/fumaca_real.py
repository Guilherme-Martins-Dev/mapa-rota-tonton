"""Teste de fumaça com dados REAIS (OSM, sem TomTom). NÃO roda no CI.

Uso: ./.venv/Scripts/python.exe scripts/fumaca_real.py
Mede download, leitura do .graphml, preparar_grafo e 3 rotas em Messejana; compara o grafo lido com o
baixado; decompõe o tempo do download (cronômetros nas etapas do osmnx e cProfile).
Faz 3 downloads (cerca de 75 s cada) e grava tudo em uma pasta temporária apagada no fim.
"""
import cProfile
import importlib
import pstats
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

import osmnx as ox
from shapely.geometry import LineString

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # roda sem instalar o pacote

from tonton import planejador  # noqa: E402
from tonton.config import LUGAR  # noqa: E402
from tonton.grafo import carregar_grafo  # noqa: E402
from tonton.planejador import Criterio  # noqa: E402
from tonton.ruas import como_lista, eh_tomtom, ponto_medio  # noqa: E402


def medir(f):
    t0 = time.perf_counter()
    r = f()
    return r, time.perf_counter() - t0


def pct(parte, total):
    return f"{100 * parte / total:.1f}%" if total else "n/d"


def comparar_grafos(G1, G2):
    """Compara baixado (G1) e lido do .graphml (G2). Devolve as diferenças (aresta, campo, valor1, valor2)."""
    print(f"    mesmo conjunto de nós: {set(G1.nodes) == set(G2.nodes)} ({G1.number_of_nodes()} e {G2.number_of_nodes()})")
    k1, k2 = set(G1.edges(keys=True)), set(G2.edges(keys=True))
    print(f"    mesmo conjunto de edges(keys=True): {k1 == k2} ({len(k1)} e {len(k2)})")
    difs = []
    for u, v, k in k1 & k2:
        a, b = G1.edges[u, v, k], G2.edges[u, v, k]
        for campo in ("length", "highway", "name", "maxspeed"):
            va, vb = a.get(campo), b.get(campo)
            igual = (va is not None and vb is not None and float(va) == float(vb)) if campo == "length" else va == vb
            if not igual:
                difs.append(((u, v, k), campo, va, vb))
    arestas_dif = {d[0] for d in difs}
    print(f"    arestas com length/highway/name/maxspeed diferentes: {len(arestas_dif)} (esperado 0)")
    for d in difs[:10]:
        print(f"        exemplo: {d}")
    return difs


def checar_listas_como_texto(G):
    """Conta valores str de highway/name/maxspeed que começam com '[' (lista virada texto)."""
    n = sum(1 for *_, d in G.edges(keys=True, data=True) for c in ("highway", "name", "maxspeed")
            if isinstance(d.get(c), str) and d[c].lstrip().startswith("["))
    print(f"    valores str de highway/name/maxspeed começando com '[': {n} (esperado 0)")
    return n


ETAPAS = [("osmnx.geocoder", "geocode_to_gdf", "geocodificar o lugar (Nominatim)"),
          ("osmnx._overpass", "_get_overpass_pause", "pausa/consulta de status do Overpass"),
          ("osmnx._overpass", "_overpass_request", "pedido ao Overpass (rede + servidor)"),
          ("osmnx.graph", "_create_graph", "JSON para grafo (parsing + construção)"),
          ("osmnx.simplification", "simplify_graph", "simplificação da topologia"),
          ("osmnx.truncate", "largest_component", "maior componente"),
          ("osmnx.distance", "add_edge_lengths", "comprimentos das arestas")]


def baixar_por_etapa():
    """Download com cada função interna do osmnx cronometrada (tempos aninhados: não somar linhas)."""
    tempos, originais = {}, []
    for modulo, nome, _ in ETAPAS:
        try:
            m = importlib.import_module(modulo)
            f = getattr(m, nome)
        except (ImportError, AttributeError):
            continue

        def embrulho(*a, _f=f, _n=nome, **k):
            t0 = time.perf_counter()
            try:
                return _f(*a, **k)
            finally:
                tempos[_n] = tempos.get(_n, 0) + time.perf_counter() - t0
        setattr(m, nome, embrulho)
        originais.append((m, nome, f))
    try:
        _, total = medir(lambda: ox.graph_from_place(LUGAR, network_type="drive"))
    finally:
        for m, nome, f in originais:
            setattr(m, nome, f)
    print(f"(e) download por etapa (cronômetros nas funções do osmnx; tempos aninhados): total {total:.2f} s")
    for _, nome, desc in ETAPAS:
        if nome in tempos:
            print(f"    {nome} [{desc}]: {tempos[nome]:.2f} s ({pct(tempos[nome], total)} do total)")
        else:
            print(f"    {nome} [{desc}]: não chamada ou não encontrada nesta versão")
    return total, tempos


def grupo(arq):
    a = arq.replace("\\", "/")
    if "/osmnx/" in a:
        return "osmnx"
    if any(f"/{p}/" in a for p in ("urllib3", "requests", "http", "ssl", "socket", "selectors", "idna", "charset_normalizer")) \
            or a.endswith(("/ssl.py", "/socket.py", "/selectors.py")) or a in ("~", "{built-in}"):
        return "rede/stdlib de E/S e funções C"
    return "outros (pandas, geopandas, shapely, networkx, json, numpy...)"


def baixar_com_perfil():
    """Download sob cProfile: tempo próprio (tottime) agrupado por origem do código."""
    pr = cProfile.Profile()
    t0 = time.perf_counter()
    pr.enable()
    ox.graph_from_place(LUGAR, network_type="drive")
    pr.disable()
    total = time.perf_counter() - t0
    st = pstats.Stats(pr)
    por_grupo, espera = Counter(), 0.0
    for (arq, _, nome), (_, _, tt, _, _) in st.stats.items():
        por_grupo[grupo(arq)] += tt
        # funções C bloqueantes: recv/read de socket, SSL, select/poll, sleep
        if arq == "~" and any(x in nome for x in ("recv", "sock", "SSL", "select", "poll", "sleep", "getaddrinfo", "connect")):
            espera += tt
    soma = sum(por_grupo.values())
    print(f"(f) download sob cProfile: {total:.2f} s (o perfilador infla o tempo de Python); tempo próprio somado: {soma:.2f} s")
    print(f"    espera bloqueante (funções C de socket/SSL/select/sleep): {espera:.2f} s ({pct(espera, soma)})")
    for k, v in por_grupo.most_common():
        print(f"    tempo próprio em {k}: {v:.2f} s ({pct(v, soma)})")
    print("    15 funções com maior tempo próprio:")
    for (arq, _, nome), (_, nc, tt, ct, _) in sorted(st.stats.items(), key=lambda kv: -kv[1][2])[:15]:
        print(f"        {tt:7.2f} s próprio  {ct:7.2f} s acumulado  {nc:7d} chamadas  {Path(arq).name}:{nome}")


def main():
    # O osmnx tem cache HTTP próprio; desligado para o download medido ser de verdade.
    ox.settings.use_cache = False
    with tempfile.TemporaryDirectory(prefix="tonton-fumaca-") as tmp:  # não mexe no cache real; apaga no fim
        executar(Path(tmp))


def executar(pasta):
    print(f"lugar: {LUGAR}")
    G_baixado, t_download = medir(lambda: carregar_grafo(LUGAR, usar_cache=False, pasta=pasta))
    print(f"(a) download sem cache (+ gravação do .graphml): {t_download:.2f} s")
    arquivo = next(pasta.glob("*.graphml"))
    print(f"    arquivo: {arquivo.name}, {arquivo.stat().st_size / 1e6:.2f} MB")

    G, t_leitura = medir(lambda: carregar_grafo(LUGAR, pasta=pasta))
    print(f"(b) leitura do .graphml (cache): {t_leitura:.2f} s")

    print("baixado x lido do .graphml:")
    comparar_grafos(G_baixado, G)
    checar_listas_como_texto(G)

    arestas = list(G.edges(keys=True, data=True))
    print(f"vértices: {G.number_of_nodes()}  arestas: {G.number_of_edges()}")

    tt = [(u, v, k) for u, v, k, d in arestas if eh_tomtom(d)]
    pontos = {ponto_medio(G, u, v, k) for u, v, k in tt}
    print(f"arestas para a TomTom: {len(tt)}  pontos médios distintos: {len(pontos)}")

    cont = Counter(h for _, _, _, d in arestas for h in como_lista(d.get("highway")))
    print("distribuição de highway (uma aresta com lista conta em cada tipo):")
    for h, n in cont.most_common():
        print(f"    {h}: {n}")
    n = len(arestas)
    sem_nome = sum(1 for *_, d in arestas if not any(str(x).strip() for x in como_lista(d.get("name"))))
    sem_max = sum(1 for *_, d in arestas if d.get("maxspeed") in (None, "", []))
    com_geom = sum(1 for *_, d in arestas if d.get("geometry") is not None)
    print(f"sem name: {pct(sem_nome, n)}  sem maxspeed: {pct(sem_max, n)}  com geometry: {pct(com_geom, n)}")

    # Tipos após o ida-e-volta pelo .graphml.
    tipos = lambda campo: dict(Counter(type(d.get(campo)).__name__ for *_, d in arestas))
    print(f"tipos: length={tipos('length')} highway={tipos('highway')} name={tipos('name')} maxspeed={tipos('maxspeed')}")
    ok_geom = all(isinstance(d["geometry"], LineString) for *_, d in arestas if d.get("geometry") is not None)
    print(f"geometry sempre LineString: {ok_geom}")

    _, t_pesos = medir(lambda: planejador.preparar_grafo(G, None))
    print(f"(c) preparar_grafo sem trânsito: {t_pesos:.2f} s")

    # Dois cruzamentos distantes: o mais ao sudoeste e o mais ao nordeste da maior componente forte.
    import networkx as nx
    comp = max(nx.strongly_connected_components(G), key=len)
    a = min(comp, key=lambda x: G.nodes[x]["y"] + G.nodes[x]["x"])
    b = max(comp, key=lambda x: G.nodes[x]["y"] + G.nodes[x]["x"])
    ya, xa, yb, xb = G.nodes[a]["y"], G.nodes[a]["x"], G.nodes[b]["y"], G.nodes[b]["x"]
    print(f"origem {a} ({ya:.5f},{xa:.5f}) -> destino {b} ({yb:.5f},{xb:.5f})")
    resumos, t_rotas = medir(lambda: planejador.planejar(G, a, b))
    print(f"(d) 3 rotas (distância, tempo, consumo): {t_rotas:.2f} s")
    print(planejador.comparar(resumos))
    for c in Criterio:
        print(f"    {c.name}: {len(resumos[c].rota.arestas)} arestas")

    baixar_por_etapa()
    baixar_com_perfil()


if __name__ == "__main__":
    main()
