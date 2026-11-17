"""Teste de fumaça com dados REAIS (OSM, sem TomTom). NÃO roda no CI.

Uso: ./.venv/Scripts/python.exe scripts/fumaca_real.py [--fonte auto|api]
Mede download, leitura do .graphml, preparar_grafo e 3 rotas em Messejana; compara o grafo lido com o
baixado; decompõe o tempo do download conforme a fonte que de fato respondeu:
  overpass: cronômetros nas etapas do osmnx e cProfile (2 downloads extras);
  api-osm:  cronômetros por etapa de `baixar_via_api_osm` (1 download extra).
--fonte auto (padrão): `carregar_grafo` tenta o Overpass e cai para a API se ele falhar.
--fonte api: pula o Overpass (simula a falha dele) e usa direto o fallback; serve para a máquina em que o
Overpass está fora do ar e para não esperar o timeout.
Grava tudo em uma pasta temporária apagada no fim.
"""
import argparse
import cProfile
import importlib
import statistics
import pstats
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

import networkx as nx
import osmnx as ox
import requests
from shapely.geometry import LineString

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # roda sem instalar o pacote

from tonton import planejador  # noqa: E402
from tonton.config import LUGAR  # noqa: E402
from tonton.grafo import baixar_via_api_osm, carregar_grafo  # noqa: E402
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


def baixar_api_por_etapa():
    """Download pela API do OSM com o tempo de cada etapa de `baixar_via_api_osm` (etapas em sequência: somam o total)."""
    tempos = {}
    _, total = medir(lambda: baixar_via_api_osm(LUGAR, tempos))
    print(f"(e) download por etapa, fonte API do OSM (NÃO comparável com os 74,5 s do Overpass): total {total:.2f} s")
    for nome, v in tempos.items():
        if nome.startswith("pedidos"):
            print(f"    {nome}: {v}")
        else:
            print(f"    {nome}: {v:.2f} s ({pct(v, total)} do total)")
    return total, tempos


# Números medidos em 2026-11-16 via Overpass (docs/dados/fumaca-real-messejana.md), para comparar com a API.
REF_OVERPASS = {"vertices": 746, "arestas": 1870, "sem_name": 8.0, "sem_maxspeed": 92.7, "com_geometry": 29.9,
                "highway": {"residential": 1568, "tertiary": 85, "primary": 64, "unclassified": 48, "secondary": 40,
                            "trunk": 39, "living_street": 14, "trunk_link": 7, "primary_link": 7}}


def descrever_grafo(G, rotulo):
    """Estatísticas para comparar fontes: tamanho, highway, % de atributos, comprimento, componentes fortes."""
    arestas = list(G.edges(keys=True, data=True))
    n = len(arestas)
    cont = Counter(h for *_, d in arestas for h in como_lista(d.get("highway")))
    sem_nome = sum(1 for *_, d in arestas if not any(str(x).strip() for x in como_lista(d.get("name"))))
    sem_max = sum(1 for *_, d in arestas if d.get("maxspeed") in (None, "", []))
    com_geom = sum(1 for *_, d in arestas if d.get("geometry") is not None)
    comp = list(nx.strongly_connected_components(G))
    comp_fracas = nx.number_weakly_connected_components(G)
    comprimentos = [float(d["length"]) for *_, d in arestas]
    print(f"[{rotulo}] vértices {G.number_of_nodes()}  arestas {n}  fonte {G.graph.get('fonte')!r}")
    print(f"    highway: {dict(cont.most_common())}")
    print(f"    sem name {pct(sem_nome, n)}  sem maxspeed {pct(sem_max, n)}  com geometry {pct(com_geom, n)}")
    print(f"    length: soma {sum(comprimentos) / 1000:.3f} km  mediana {statistics.median(comprimentos):.2f} m  "
          f"média {statistics.mean(comprimentos):.2f} m  máx {max(comprimentos):.1f} m")
    print(f"    componentes fortemente conexas: {len(comp)} (maior: {max(map(len, comp))} vértices); "
          f"fracamente conexas: {comp_fracas}")
    print(f"    referência Overpass (2026-11-16): {REF_OVERPASS['vertices']} vértices, {REF_OVERPASS['arestas']} arestas, "
          f"sem name {REF_OVERPASS['sem_name']}%, sem maxspeed {REF_OVERPASS['sem_maxspeed']}%, "
          f"com geometry {REF_OVERPASS['com_geometry']}%")
    dif = {h: (cont.get(h, 0), r) for h, r in REF_OVERPASS["highway"].items() if cont.get(h, 0) != r}
    dif.update({h: (v, 0) for h, v in cont.items() if h not in REF_OVERPASS["highway"]})
    print(f"    highway diferente da referência (agora, referência): {dif or 'nenhum'}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fonte", choices=("auto", "api"), default="auto")
    args = ap.parse_args()
    # O osmnx tem cache HTTP próprio; desligado para o download medido ser de verdade.
    ox.settings.use_cache = False
    if args.fonte == "api":
        def overpass_fora(*a, **k):
            raise requests.exceptions.ConnectTimeout("Overpass pulado por --fonte api (simulação)")
        ox.graph_from_place = overpass_fora
    with tempfile.TemporaryDirectory(prefix="tonton-fumaca-") as tmp:  # não mexe no cache real; apaga no fim
        executar(Path(tmp))


def executar(pasta):
    print(f"lugar: {LUGAR}")
    G_baixado, t_download = medir(lambda: carregar_grafo(LUGAR, usar_cache=False, pasta=pasta))
    fonte = G_baixado.graph.get("fonte")
    print(f"(a) download sem cache (+ gravação do .graphml), fonte {fonte!r}: {t_download:.2f} s")
    arquivo = next(pasta.glob("*.graphml"))
    print(f"    arquivo: {arquivo.name}, {arquivo.stat().st_size / 1e6:.2f} MB")

    G, t_leitura = medir(lambda: carregar_grafo(LUGAR, pasta=pasta))
    print(f"(b) leitura do .graphml (cache): {t_leitura:.2f} s")

    print("baixado x lido do .graphml:")
    comparar_grafos(G_baixado, G)
    checar_listas_como_texto(G)
    print(f"    fonte gravada no .graphml e lida de volta: {G.graph.get('fonte')!r}")

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

    descrever_grafo(G, "grafo lido")
    if fonte == "overpass":
        for medicao in (baixar_por_etapa, baixar_com_perfil):
            try:
                medicao()
            except requests.exceptions.RequestException as erro:  # Overpass é intermitente: não perde o que já saiu
                print(f"    {medicao.__name__}: NÃO MEDIDO, Overpass falhou ({type(erro).__name__}: {str(erro)[:120]})")
    else:
        baixar_api_por_etapa()


if __name__ == "__main__":
    main()
