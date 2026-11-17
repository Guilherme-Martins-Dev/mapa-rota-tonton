import math
from typing import Callable

from tonton.ruas import eh_tomtom, ponto_medio

# Velocidade (km/h) usada quando a via não tem maxspeed no OSM.
VELOCIDADE_PADRAO = {
    "motorway": 80, "trunk": 60, "primary": 50, "secondary": 40, "tertiary": 40,
    "residential": 30, "living_street": 20, "service": 20, "unclassified": 30,
}
VELOCIDADE_GERAL = 30


def ler_maxspeed(valor) -> float | None:
    """'40', '40 km/h', ['30', '50'] -> km/h (a menor da lista); mph convertido; inválido -> None."""
    if valor is None:
        return None
    itens = valor if isinstance(valor, (list, tuple, set)) else [valor]
    achadas = []
    for item in itens:
        texto = str(item).strip().lower()
        digitos = "".join(c for c in texto.split()[0] if c.isdigit() or c == ".") if texto else ""
        if not digitos:
            continue
        v = float(digitos)
        if "mph" in texto:
            v *= 1.609344
        if v > 0:
            achadas.append(v)
    return min(achadas) if achadas else None


def velocidade_livre_osm(dados_aresta: dict) -> float:
    """maxspeed do OSM; sem ele, padrão do tipo de via (km/h)."""
    v = ler_maxspeed(dados_aresta.get("maxspeed"))
    if v is not None:
        return v
    hw = dados_aresta.get("highway")
    for h in (hw if isinstance(hw, (list, tuple)) else [hw]):
        if h in VELOCIDADE_PADRAO:
            return float(VELOCIDADE_PADRAO[h])
    return float(VELOCIDADE_GERAL)


def tempo(comprimento_m: float | None, velocidade_kmh: float | None) -> float:
    """t = comprimento / velocidade, em segundos. Sem dado ou velocidade <= 0: inf."""
    if comprimento_m is None or not velocidade_kmh or velocidade_kmh <= 0:
        return math.inf
    return comprimento_m / (velocidade_kmh / 3.6)


def _velocidades_tomtom(fluxo: dict) -> tuple[float, float] | None:
    """(v_livre, v_atual) em km/h do fluxo da TomTom; None se vier incompleto."""
    try:
        livre, atual = float(fluxo["freeFlowSpeed"]), float(fluxo["currentSpeed"])
    except (KeyError, TypeError, ValueError):
        return None
    return (livre, atual) if livre > 0 and atual > 0 else None


def gravar_velocidades(dados: dict, v_livre: float, v_atual: float) -> None:
    """Grava na aresta v_livre, v_atual (km/h), t_livre e t_atual (s)."""
    comp = dados.get("length")
    dados.update(
        v_livre=v_livre, v_atual=v_atual,
        t_livre=tempo(comp, v_livre), t_atual=tempo(comp, v_atual),
    )


def atribuir_pesos(G, consultar: Callable[[float, float], dict] | None = None):
    """Grava em cada aresta v_livre, v_atual (km/h), t_livre e t_atual (s).

    Só vias trunk/primary/secondary/tertiary são consultadas (cota da API), uma vez por ponto
    médio. Falha na consulta ou via sem TomTom: v_atual = v_livre (fallback). Devolve G.
    """
    cache: dict[tuple[float, float], tuple[float, float] | None] = {}
    for u, v, chave, dados in G.edges(keys=True, data=True):
        v_livre = v_atual = velocidade_livre_osm(dados)
        if consultar is not None and eh_tomtom(dados):
            ponto = ponto_medio(G, u, v, chave)
            if ponto not in cache:
                try:
                    cache[ponto] = _velocidades_tomtom(consultar(*ponto))
                except Exception:
                    cache[ponto] = None
            if cache[ponto] is not None:
                v_livre, v_atual = cache[ponto]
        gravar_velocidades(dados, v_livre, v_atual)
    return G
