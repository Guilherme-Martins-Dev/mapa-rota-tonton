"""Etapa 5: planejador. Escolhe a rota por menor distância, menor tempo ou menor consumo.

Cada rota é otimizada por um peso (Dijkstra da etapa 3), mas distância, tempo e litros são
sempre somados sobre as arestas escolhidas, para comparar os três critérios com justiça.
"""
import math
import re
from dataclasses import dataclass
from enum import Enum

from tonton import consumo, pesos
from tonton.consumo import PADRAO, Veiculo
from tonton.rotas import Rota, menor_rota
from tonton.ruas import buscar_rua


class Criterio(Enum):
    DISTANCIA = "length"  # metros
    TEMPO = "t_atual"     # segundos
    CONSUMO = "litros"    # litros


@dataclass(frozen=True)
class Resumo:
    criterio: Criterio
    rota: Rota
    distancia_km: float
    tempo_min: float  # t_atual somado
    litros: float


def preparar_grafo(G, consultar=None, veiculo: Veiculo = PADRAO):
    """Grava os pesos (length, t_livre, t_atual, litros) no grafo. consultar=None: sem TomTom."""
    pesos.atribuir_pesos(G, consultar)
    consumo.atribuir_consumo(G, veiculo)
    return G


def _haversine_m(lat1, lon1, lat2, lon2) -> float:
    """Distância em metros entre dois pontos (graus)."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(a))


def vertice_mais_proximo(G, lat: float, lon: float):
    """Cruzamento mais próximo da coordenada (lat, lon), por distância haversine."""
    if G.number_of_nodes() == 0:
        raise ValueError("grafo vazio")
    return min(G.nodes, key=lambda n: _haversine_m(lat, lon, G.nodes[n]["y"], G.nodes[n]["x"]))


_NUM = r"[-+]?\d+(?:\.\d+)?"
_COORD = re.compile(rf"^\s*({_NUM})\s*,\s*({_NUM})\s*$")


def resolver_ponto(G, texto: str):
    """Cruzamento para "lat,lon" ou nome de rua (primeiro trecho achado; usa o cruzamento seguinte)."""
    m = _COORD.match(texto)
    if m:
        lat, lon = float(m.group(1)), float(m.group(2))
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError(f"coordenada fora do intervalo: {texto!r}")
        return vertice_mais_proximo(G, lat, lon)
    achados = buscar_rua(G, texto)
    if not achados:
        raise ValueError(f"rua não encontrada: {texto!r}")
    return achados[0].proximo


def _finito(valor, nome, aresta):
    if valor is None or not math.isfinite(valor):
        raise ValueError(f"aresta {aresta} sem '{nome}' finito: {valor}")
    return valor


def _resumir(G, criterio: Criterio, rota: Rota) -> Resumo:
    metros = segundos = litros = 0.0
    for u, v, k in rota.arestas:
        d = G[u][v][k]
        metros += _finito(d.get("length"), "length", (u, v, k))
        segundos += _finito(d.get("t_atual"), "t_atual", (u, v, k))
        litros += _finito(d.get("litros"), "litros", (u, v, k))
    return Resumo(criterio, rota, metros / 1000, segundos / 60, litros)


def planejar(G, origem, destino, criterio: Criterio | None = None, veiculo: Veiculo = PADRAO) -> dict:
    """Rotas por critério: {Criterio: Resumo}. criterio=None calcula os três.

    Exige preparar_grafo antes. `veiculo` só vale ali (os litros já estão nas arestas).
    """
    criterios = list(Criterio) if criterio is None else [criterio]
    return {c: _resumir(G, c, menor_rota(G, origem, destino, peso=c.value)) for c in criterios}


_ROTULO = {Criterio.DISTANCIA: "menor distância", Criterio.TEMPO: "menor tempo", Criterio.CONSUMO: "menor consumo"}


def comparar(resumos: dict) -> str:
    """Tabela em texto, uma linha por critério; '*' marca o melhor de cada coluna."""
    if not resumos:
        return ""
    campos = ("distancia_km", "tempo_min", "litros")
    melhor = {c: min(getattr(r, c) for r in resumos.values()) for c in campos}

    def celula(r, campo, unidade):
        v = getattr(r, campo)
        return f"{v:8.2f} {unidade}{'*' if v == melhor[campo] else ' '}"

    linhas = [f"{'critério':<16}{'distância':>12}  {'tempo':>12}  {'consumo':>12}"]
    for c, r in resumos.items():
        linhas.append(
            f"{_ROTULO[c]:<16}{celula(r, 'distancia_km', 'km')}  "
            f"{celula(r, 'tempo_min', 'min')}  {celula(r, 'litros', 'L')}"
        )
    linhas.append("* = melhor da coluna")
    return "\n".join(linhas)


def _coordenadas(G, resumo: Resumo) -> list:
    """Pontos [lon, lat] da rota: geometria das arestas, ou vértices quando não há."""
    pontos = []
    for u, v, k in resumo.rota.arestas:
        geom = G[u][v][k].get("geometry")
        if geom is not None:
            trecho = [[x, y] for x, y in geom.coords]
            # a geometria nem sempre vem de u para v: se a ponta inicial está mais perto de v, inverte
            ux, uy, vx, vy = G.nodes[u]["x"], G.nodes[u]["y"], G.nodes[v]["x"], G.nodes[v]["y"]
            ini, fim = trecho[0], trecho[-1]
            if (ini[0] - vx) ** 2 + (ini[1] - vy) ** 2 < (ini[0] - ux) ** 2 + (ini[1] - uy) ** 2 and \
                    (fim[0] - ux) ** 2 + (fim[1] - uy) ** 2 < (fim[0] - vx) ** 2 + (fim[1] - vy) ** 2:
                trecho.reverse()
        else:
            trecho = [[G.nodes[u]["x"], G.nodes[u]["y"]], [G.nodes[v]["x"], G.nodes[v]["y"]]]
        pontos.extend(trecho[1:] if pontos and pontos[-1] == trecho[0] else trecho)
    if not pontos:  # origem == destino
        n = resumo.rota.vertices[0]
        pontos = [[G.nodes[n]["x"], G.nodes[n]["y"]]] * 2  # LineString exige 2 pontos
    return pontos


def geojson(G, resumo: Resumo) -> dict:
    """Feature GeoJSON (LineString [lon, lat]) da rota, com os totais em properties."""
    return {
        "type": "Feature",
        "geometry": {"type": "LineString", "coordinates": _coordenadas(G, resumo)},
        "properties": {
            "criterio": resumo.criterio.name.lower(),
            "distancia_km": resumo.distancia_km,
            "tempo_min": resumo.tempo_min,
            "litros": resumo.litros,
        },
    }
