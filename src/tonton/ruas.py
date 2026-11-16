import re
import unicodedata
from dataclasses import dataclass
from typing import Iterator

from shapely.geometry import LineString

from tonton.grafo import HIGHWAYS_TOMTOM


@dataclass(frozen=True)
class Trecho:
    u: int                       # cruzamento de origem
    v: int                       # cruzamento seguinte
    chave: int                   # key do MultiDiGraph (ruas paralelas)
    nomes: tuple[str, ...]       # vazio se a rua não tem nome
    highway: tuple[str, ...]     # sempre tupla normalizada
    comprimento: float | None    # metros (atributo length); None se ausente
    meio: tuple[float, float]    # (lat, lon) do ponto médio da geometria
    proximo: int                 # = v, cruzamento onde o trajeto recomeça


def como_lista(valor) -> list:
    """None -> [], str -> [str], list/tuple/set -> list. Normaliza name/highway."""
    if valor is None:
        return []
    if isinstance(valor, str):
        return [valor]
    if isinstance(valor, (list, tuple, set, frozenset)):
        return list(valor)
    return [valor]


def normalizar(texto: str) -> str:
    """Minúsculas (casefold), sem acentos (NFKD), espaços colapsados e aparados."""
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFKD", str(texto)) if not unicodedata.combining(c)
    )
    return re.sub(r"\s+", " ", sem_acento.casefold()).strip()


def _nomes(dados_aresta: dict) -> tuple[str, ...]:
    """Nomes não vazios e sem duplicados, na ordem original."""
    vistos = []
    for n in como_lista(dados_aresta.get("name")):
        n = str(n).strip()
        if n and n not in vistos:
            vistos.append(n)
    return tuple(vistos)


def _highways(dados_aresta: dict) -> tuple[str, ...]:
    return tuple(str(h) for h in como_lista(dados_aresta.get("highway")))


def tem_nome(dados_aresta: dict, busca: str | None = None) -> bool:
    """Sem busca: a aresta tem ao menos um nome não vazio.
    Com busca: algum nome normalizado contém a busca normalizada."""
    nomes = _nomes(dados_aresta)
    if busca is None:
        return bool(nomes)
    alvo = normalizar(busca)
    if not alvo:
        raise ValueError("A busca não pode ser vazia.")
    return any(alvo in normalizar(n) for n in nomes)


def eh_tomtom(dados_aresta: dict) -> bool:
    """True se qualquer highway da aresta está em HIGHWAYS_TOMTOM."""
    return any(h in HIGHWAYS_TOMTOM for h in _highways(dados_aresta))


def ponto_medio(G, u, v, chave) -> tuple[float, float]:
    """(lat, lon) do ponto a metade do comprimento ao longo da geometria;
    sem 'geometry', ponto médio do segmento entre os nós u e v."""
    geom = G.edges[u, v, chave].get("geometry")
    if geom is None:
        geom = LineString([(G.nodes[u]["x"], G.nodes[u]["y"]), (G.nodes[v]["x"], G.nodes[v]["y"])])
    if geom.length == 0:
        p = geom.coords[0]
    else:
        p = geom.interpolate(0.5, normalized=True).coords[0]
    return (p[1], p[0])  # x é lon, y é lat


def trechos(G, so_tomtom: bool = False) -> Iterator[Trecho]:
    """Um Trecho por aresta (u, v, key). so_tomtom=True filtra por HIGHWAYS_TOMTOM."""
    for u, v, chave, dados in G.edges(keys=True, data=True):
        if so_tomtom and not eh_tomtom(dados):
            continue
        comp = dados.get("length")
        yield Trecho(
            u=u, v=v, chave=chave,
            nomes=_nomes(dados),
            highway=_highways(dados),
            comprimento=float(comp) if comp is not None else None,
            meio=ponto_medio(G, u, v, chave),
            proximo=v,
        )


def buscar_rua(G, nome: str, so_tomtom: bool = False) -> list[Trecho]:
    """Todos os trechos cujo nome casa com a busca (sem acento e sem caixa)."""
    alvo = normalizar(nome)
    if not alvo:
        raise ValueError("A busca não pode ser vazia.")
    return [t for t in trechos(G, so_tomtom) if any(alvo in normalizar(n) for n in t.nomes)]


def agrupar_por_rua(G, so_tomtom: bool = False) -> dict[str, list[Trecho]]:
    """Chave = nome original (primeiro nome); trechos sem nome ficam fora."""
    grupos: dict[str, list[Trecho]] = {}
    for t in trechos(G, so_tomtom):
        if t.nomes:
            grupos.setdefault(t.nomes[0], []).append(t)
    return grupos
