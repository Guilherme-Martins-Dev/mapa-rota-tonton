import re
import time
import unicodedata
from pathlib import Path

import osmnx as ox

from tonton.config import CACHE, LUGAR


# Tipos de via consultados na TomTom (o quadro lista só estes quatro).
HIGHWAYS_TOMTOM = frozenset({"trunk", "primary", "secondary", "tertiary"})


def slug(lugar: str) -> str:
    """'Messejana, Fortaleza, Ceará' -> 'messejana-fortaleza-ceara' (minúsculas, sem acento, [a-z0-9-])."""
    sem_acento = "".join(c for c in unicodedata.normalize("NFKD", lugar) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", sem_acento.lower()).strip("-")


def arquivo_cache(lugar: str = LUGAR, pasta: Path = CACHE) -> Path:
    return Path(pasta) / f"grafo-{slug(lugar)}.graphml"


def _cache_valido(caminho: Path, validade_dias: float) -> bool:
    return caminho.is_file() and (time.time() - caminho.stat().st_mtime) < validade_dias * 86400


def carregar_grafo(lugar: str = LUGAR, usar_cache: bool = True, validade_dias: float = 30, pasta: Path = CACHE):
    """Grafo viário DIRIGIDO (mão única) e MULTI (ruas paralelas): vértices = cruzamentos, arestas = trechos.

    Com cache em disco (.graphml): lê o arquivo se existir e for mais novo que `validade_dias`; se faltar,
    expirou ou estiver corrompido, baixa do OSM e regrava (atômico: .tmp + replace). Só o grafo BRUTO do
    OSM vai para o disco; pesos (t_livre, t_atual, litros) são calculados depois e nunca são gravados.
    usar_cache=False força o download e regrava o arquivo.

    Tipos após o ida-e-volta (conferido com osmnx 2.1.2 em Messejana): length vira float; geometry vira
    LineString; highway/name continuam list quando a aresta tem vários valores (str quando tem um);
    maxspeed continua str ou list de str; x/y dos vértices são float. Ver scripts/fumaca_real.py.
    """
    caminho = arquivo_cache(lugar, pasta)
    if usar_cache and _cache_valido(caminho, validade_dias):
        try:
            return ox.load_graphml(caminho)
        except Exception:
            pass  # arquivo corrompido: baixa de novo
    G = ox.graph_from_place(lugar, network_type="drive")
    caminho.parent.mkdir(parents=True, exist_ok=True)
    tmp = caminho.with_name(caminho.name + ".tmp")
    try:
        ox.save_graphml(G, tmp)
        tmp.replace(caminho)
    except BaseException:
        tmp.unlink(missing_ok=True)  # não deixa .tmp parcial
        raise
    return G


def tabelas(G):
    """Tabela de vértices (y=latitude, x=longitude) e de arestas (nome, comprimento, highway, maxspeed)."""
    return ox.graph_to_gdfs(G)
