"""CLI: python -m tonton --origem "..." --destino "..." [--criterio ...] [--alternativas K] [--geojson arq] [--mostrar] [--atualizar-grafo]."""
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
    p.add_argument("--alternativas", type=int, default=1, metavar="K",
                   help="K rotas distintas por critério (K>=1; 1 = só a melhor)")
    p.add_argument("--max-sobreposicao", type=float, default=0.8, metavar="F",
                   help="fração máxima (0 a 1) que uma alternativa pode repetir de outra rota (padrão 0.8)")
    p.add_argument("--geojson", metavar="ARQUIVO", help="grava as rotas em GeoJSON")
    p.add_argument("--mostrar", action="store_true", help="desenha as rotas no mapa")
    p.add_argument("--atualizar-grafo", action="store_true", help="baixa o grafo do OSM de novo e regrava o cache")
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
    rotas, cor_rotas = [], []
    for c, r in resumos.items():
        for i, resumo in enumerate(r if isinstance(r, list) else [r]):  # lista = alternativas do critério
            rotas.append(resumo.rota.vertices)
            cor_rotas.append(cores[c] if i == 0 else f"C{(i + 2) % 10}")  # alternativas: cores do ciclo padrão
    ox.plot_graph_routes(G, rotas, route_colors=cor_rotas, show=False, close=False)
    plt.show()


def main(argv=None, carregar=carregar_grafo, consultar_factory=consultar_padrao, exibir=mostrar) -> int:
    """Roda o fluxo completo. Devolve o código de saída (0 ok, 2 erro de uso/dados)."""
    args = _parser().parse_args(_juntar_valores(argv))
    if args.alternativas < 1:
        print("erro: --alternativas deve ser >= 1", file=sys.stderr)
        return 2
    if not 0 <= args.max_sobreposicao <= 1:
        print("erro: --max-sobreposicao deve estar entre 0 e 1", file=sys.stderr)
        return 2
    try:
        consultar = None if args.sem_transito else consultar_factory()
    except RuntimeError as e:
        print(f"erro: {e}\nDefina TOMTOM_KEY ou use --sem-transito.", file=sys.stderr)
        return 2
    try:
        G = planejador.preparar_grafo(carregar(usar_cache=False) if args.atualizar_grafo else carregar(), consultar)
        origem = planejador.resolver_ponto(G, args.origem)
        destino = planejador.resolver_ponto(G, args.destino)
        criterio = None if args.criterio == "todos" else CRITERIOS[args.criterio]
        if args.alternativas == 1:
            resumos = planejador.planejar(G, origem, destino, criterio)
        else:  # {Criterio: [Resumo]}: a ótima em [0] e as alternativas depois
            resumos = {c: planejador.planejar_alternativas(G, origem, destino, c, args.alternativas,
                                                           args.max_sobreposicao)
                       for c in ([criterio] if criterio else list(Criterio))}
    except (ValueError, RotaInexistente) as e:  # RotaInexistente é ValueError
        print(f"erro: {e}", file=sys.stderr)
        return 2
    if args.alternativas == 1:
        print(planejador.comparar(resumos))
        colecao = {"type": "FeatureCollection", "features": [planejador.geojson(G, r) for r in resumos.values()]}
    else:
        features = []
        for c, lista in resumos.items():
            print(f"[{c.name.lower()}] {len(lista)} rota(s)\n{planejador.comparar(lista)}")
            features += planejador.geojson_colecao(G, lista)["features"]  # `indice` vale dentro de cada critério
        colecao = {"type": "FeatureCollection", "features": features}
    if args.geojson:
        with open(args.geojson, "w", encoding="utf-8") as f:
            json.dump(colecao, f, ensure_ascii=False)
        print(f"GeoJSON gravado em {args.geojson}")
    if args.mostrar:
        exibir(G, resumos)
    return 0
