"""CLI: python -m tonton --origem "..." --destino "..." [--criterio ...] [--geojson arq] [--mostrar]."""
import argparse
import json
import sys

from tonton import planejador, transito
from tonton.config import tomtom_key
from tonton.grafo import carregar_grafo
from tonton.planejador import Criterio
from tonton.rotas import RotaInexistente

CRITERIOS = {"distancia": Criterio.DISTANCIA, "tempo": Criterio.TEMPO, "consumo": Criterio.CONSUMO}


def consultar_padrao():
    """Consulta TomTom com cache em disco. Sem TOMTOM_KEY levanta RuntimeError."""
    tomtom_key()
    return transito.com_cache()


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="tonton", description="Planeja rotas em Messejana.")
    p.add_argument("--origem", required=True, help='"lat,lon" ou nome de rua')
    p.add_argument("--destino", required=True, help='"lat,lon" ou nome de rua')
    p.add_argument("--criterio", choices=[*CRITERIOS, "todos"], default="todos")
    p.add_argument("--geojson", metavar="ARQUIVO", help="grava as rotas em GeoJSON")
    p.add_argument("--mostrar", action="store_true", help="desenha as rotas no mapa")
    p.add_argument("--sem-transito", action="store_true", help="não consulta a TomTom")
    return p


def _juntar_valores(argv):
    """'--origem -3.8,-38.5' -> '--origem=-3.8,-38.5': sem isso o argparse lê a latitude negativa como opção."""
    argv = list(sys.argv[1:] if argv is None else argv)
    saida, i = [], 0
    while i < len(argv):
        if argv[i] in ("--origem", "--destino") and i + 1 < len(argv):
            saida.append(f"{argv[i]}={argv[i + 1]}")
            i += 2
        else:
            saida.append(argv[i])
            i += 1
    return saida


def mostrar(G, resumos):
    """Desenha as rotas (imports preguiçosos: matplotlib/osmnx só se pedido)."""
    import matplotlib.pyplot as plt
    import osmnx as ox

    cores = {Criterio.DISTANCIA: "tab:blue", Criterio.TEMPO: "tab:red", Criterio.CONSUMO: "tab:green"}
    rotas = [r.rota.vertices for r in resumos.values()]
    ox.plot_graph_routes(G, rotas, route_colors=[cores[c] for c in resumos], show=False, close=False)
    plt.show()


def main(argv=None, carregar=carregar_grafo, consultar_factory=consultar_padrao, exibir=mostrar) -> int:
    """Roda o fluxo completo. Devolve o código de saída (0 ok, 2 erro de uso/dados)."""
    args = _parser().parse_args(_juntar_valores(argv))
    try:
        consultar = None if args.sem_transito else consultar_factory()
    except RuntimeError as e:
        print(f"erro: {e}\nDefina TOMTOM_KEY ou use --sem-transito.", file=sys.stderr)
        return 2
    try:
        G = planejador.preparar_grafo(carregar(), consultar)
        origem = planejador.resolver_ponto(G, args.origem)
        destino = planejador.resolver_ponto(G, args.destino)
        criterio = None if args.criterio == "todos" else CRITERIOS[args.criterio]
        resumos = planejador.planejar(G, origem, destino, criterio)
    except (ValueError, RotaInexistente) as e:  # RotaInexistente é ValueError
        print(f"erro: {e}", file=sys.stderr)
        return 2
    print(planejador.comparar(resumos))
    if args.geojson:
        colecao = {"type": "FeatureCollection", "features": [planejador.geojson(G, r) for r in resumos.values()]}
        with open(args.geojson, "w", encoding="utf-8") as f:
            json.dump(colecao, f, ensure_ascii=False)
        print(f"GeoJSON gravado em {args.geojson}")
    if args.mostrar:
        exibir(G, resumos)
    return 0
