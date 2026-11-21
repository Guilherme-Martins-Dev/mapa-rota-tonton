"""Gera os GeoJSON do front (front/public/data) a partir do grafo em cache de Messejana.

O trânsito é SIMULADO (v_atual = v_livre x fator em [0,5; 1,0] nas arestas TomTom, semente fixa);
a TomTom NÃO é chamada. Sem isso os três critérios coincidem na rota, e a página não teria o que comparar.
O script procura, entre pares sorteados, o primeiro em que as três rotas são distintas.

Uso: python scripts/exportar_front.py
"""
import json
import random
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from tonton import planejador  # noqa: E402
from tonton.consumo import atribuir_consumo  # noqa: E402
from tonton.grafo import carregar_grafo  # noqa: E402
from tonton.pesos import atribuir_pesos, gravar_velocidades  # noqa: E402
from tonton.ruas import eh_tomtom  # noqa: E402

SEMENTE = 7
SAIDA = RAIZ / "front" / "public" / "data"


def preparar():
    G = carregar_grafo()
    atribuir_pesos(G)
    rng = random.Random(SEMENTE)
    for _, _, dados in G.edges(data=True):
        if eh_tomtom(dados):
            v = dados["v_livre"]
            gravar_velocidades(dados, v, v * rng.uniform(0.5, 1.0))
    atribuir_consumo(G)
    return G


def assinatura(G, resumo):
    return tuple(map(tuple, planejador.geojson(G, resumo)["geometry"]["coordinates"]))


def main():
    G = preparar()
    rng = random.Random(SEMENTE)
    nos = list(G.nodes)
    for _ in range(4000):
        o, d = rng.sample(nos, 2)
        try:
            r = planejador.planejar(G, o, d)
        except Exception:
            continue
        sigs = {assinatura(G, x) for x in r.values()}
        km = next(iter(r.values())).distancia_km
        if len(sigs) == 3 and 2.5 <= km <= 6:
            colecao = planejador.geojson_colecao(G, list(r.values()))
            SAIDA.mkdir(parents=True, exist_ok=True)
            (SAIDA / "rotas.geojson").write_text(json.dumps(colecao), encoding="utf-8")
            for x in r.values():
                print(f"{x.criterio.name.lower():10s} {x.distancia_km:5.2f} km  {x.tempo_min:5.1f} min  {x.litros:5.3f} L")
            print(f"origem {G.nodes[o]['y']:.5f},{G.nodes[o]['x']:.5f}  destino {G.nodes[d]['y']:.5f},{G.nodes[d]['x']:.5f}")
            return
    print("nenhum par com três rotas distintas encontrado", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
