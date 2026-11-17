import logging
import re
import tempfile
import time
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path

import osmnx as ox
import requests
from osmnx import _overpass
from osmnx._errors import ResponseStatusCodeError

from tonton.config import CACHE, LUGAR

log = logging.getLogger("tonton")

# Falhas de rede/servidor do Overpass que justificam a fonte alternativa (erro de programação NÃO entra).
ERROS_DE_REDE = (requests.exceptions.RequestException, ResponseStatusCodeError)

URL_API_OSM = "https://api.openstreetmap.org/api/0.6/map"
USER_AGENT = "tonton/0.1 (https://github.com/Guilherme-Martins-Dev/mapa-rota-tonton)"
LIMITE_AREA_API = 0.25  # grau² (limite da API v0.6 do OSM; acima disso a API responde 400)
MAX_NIVEL_BISSECAO = 3  # a API também recusa (400) mais de 50.000 nós: divide o bbox em 4 até 3 vezes
# Pior caso: 1 + 4 + 16 + 64 = 85 pedidos (64 aceitos, só no nível 3). Em Messejana foram 21.
PAUSA_ENTRE_GETS_S = 0.5  # cortesia com a API do OSM: espera antes de cada pedido filho da divisão


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

    Fonte do download: Overpass (`ox.graph_from_place`); se ele falhar por rede/servidor, cai para a API do
    OSM (`baixar_via_api_osm`). A fonte fica em `G.graph["fonte"]` ("overpass" ou "api-osm"), também no .graphml.

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
    try:
        G = ox.graph_from_place(lugar, network_type="drive")
        G.graph["fonte"] = "overpass"
    except ERROS_DE_REDE as erro:
        log.warning("Overpass indisponível (%s: %s); usando a API do OSM como fonte alternativa.",
                    type(erro).__name__, erro)
        G = baixar_via_api_osm(lugar)  # G.graph["fonte"] == "api-osm"
    caminho.parent.mkdir(parents=True, exist_ok=True)
    tmp = caminho.with_name(caminho.name + ".tmp")
    try:
        ox.save_graphml(G, tmp)
        tmp.replace(caminho)
    except BaseException:
        tmp.unlink(missing_ok=True)  # não deixa .tmp parcial
        raise
    return G


def _regras_drive():
    """Regras do `network_type="drive"` lidas do filtro Overpass da versão instalada do osmnx.

    O filtro é uma sequência de `["chave"]` (tag presente) e `["chave"!~"regex"]` (tag ausente OU sem casar
    com a regex; na Overpass a regex NÃO é ancorada, por isso `re.search`).
    """
    filtro = _overpass._get_network_filter("drive")
    regras = re.findall(r'\["([^"]+)"(?:!~"([^"]*)")?\]', filtro)
    if not any(chave == "highway" and padrao for chave, padrao in regras):
        raise RuntimeError(f"formato inesperado do filtro 'drive' do osmnx: {filtro}")
    return [(chave, re.compile(padrao) if padrao else None) for chave, padrao in regras]


def _via_de_carro(tags, regras) -> bool:
    for chave, padrao in regras:
        if padrao is None:
            if chave not in tags:  # ["highway"]: precisa existir
                return False
        elif chave in tags and padrao.search(tags[chave]):
            return False
    return True


def _filtrar_xml(respostas: list[bytes]) -> bytes:
    """Une as respostas (sem duplicar por id), mantém só os ways de carro (regra do `drive`) e os nós que usam."""
    regras = _regras_drive()
    nos, ways = {}, {}
    for xml in respostas:
        raiz = ET.fromstring(xml)
        nos.update((n.get("id"), n) for n in raiz.iter("node"))
        ways.update((w.get("id"), w) for w in raiz.iter("way"))
    ways = [w for w in ways.values() if _via_de_carro({t.get("k"): t.get("v") for t in w.iter("tag")}, regras)]
    usados = {nd.get("ref") for w in ways for nd in w.iter("nd")}
    novo = ET.Element("osm", {"version": "0.6"})
    novo.extend(n for i, n in nos.items() if i in usados)
    novo.extend(ways)
    return ET.tostring(novo, encoding="utf-8", xml_declaration=True)


def _baixar_bbox(oeste, sul, leste, norte, tempos, nivel=0, max_nivel=MAX_NIVEL_BISSECAO) -> list[bytes]:
    """GET /map do bbox; se a API disser 'too many nodes' (400), divide em 4 e baixa cada quarto.

    Os pedidos filhos esperam PAUSA_ENTRE_GETS_S antes de sair; o primeiro pedido não espera.
    """
    if nivel > 0:
        time.sleep(PAUSA_ENTRE_GETS_S)
    resp = requests.get(URL_API_OSM, params={"bbox": f"{oeste},{sul},{leste},{norte}"},
                        headers={"User-Agent": USER_AGENT}, timeout=ox.settings.requests_timeout)
    tempos["pedidos GET"] = tempos.get("pedidos GET", 0) + 1
    if resp.status_code == 400:
        if nivel >= max_nivel:
            raise ValueError(f"a API do OSM seguiu recusando (400) com o bbox dividido {nivel} vezes: "
                             f"{resp.text.strip()[:200]}")
        meio_x, meio_y = (oeste + leste) / 2, (sul + norte) / 2
        partes = [(oeste, sul, meio_x, meio_y), (meio_x, sul, leste, meio_y),
                  (oeste, meio_y, meio_x, norte), (meio_x, meio_y, leste, norte)]
        return [r for p in partes for r in _baixar_bbox(*p, tempos, nivel + 1, max_nivel)]
    resp.raise_for_status()
    return [resp.content]


def baixar_via_api_osm(lugar: str = LUGAR, tempos: dict | None = None):
    """Grafo viário de `lugar` pela API do OSM v0.6 (GET /map?bbox), quando o Overpass não responde.

    Mesmos passos do `graph_from_place` do osmnx 2.x: polígono do Nominatim, buffer de 500 m, grafo, recorte
    pelo buffer, maior componente, simplificação, recorte pelo polígono, maior componente, `street_count`.
    A diferença é a origem dos dados: a API devolve TODOS os ways, então o filtro do `network_type="drive"`
    é reaplicado aqui (`_filtrar_xml`). Limites da API: bbox até 0,25 grau² (maior que isso levanta ValueError, sem tentar dividir) e até
    50.000 nós por pedido (400): nesse caso o bbox é dividido em quartos (até MAX_NIVEL_BISSECAO vezes) e as
    respostas são unidas por id. `tempos` (dict opcional) recebe segundos por etapa e o nº de pedidos.
    """
    tempos = {} if tempos is None else tempos
    t0 = time.perf_counter()

    def marca(nome):
        nonlocal t0
        agora = time.perf_counter()
        tempos[nome] = tempos.get(nome, 0) + agora - t0
        t0 = agora

    poligono = ox.geocoder.geocode_to_gdf(lugar).union_all()
    marca("geocodificar (Nominatim)")
    proj, crs = ox.projection.project_geometry(poligono)
    buffer, _ = ox.projection.project_geometry(proj.buffer(500), crs=crs, to_latlong=True)
    oeste, sul, leste, norte = buffer.bounds
    area = (leste - oeste) * (norte - sul)
    if area > LIMITE_AREA_API:
        raise ValueError(f"{lugar!r}: bbox de {area:.3f} grau² passa do limite de {LIMITE_AREA_API} da API do OSM; "
                         "a fonte alternativa só divide o bbox quando a API recusa por excesso de nós, não quando a área passa do limite "
                         "(use o Overpass ou um lugar menor).")

    respostas = _baixar_bbox(oeste, sul, leste, norte, tempos)
    tempos["pedidos aceitos"] = len(respostas)
    marca("GET do XML (API OSM)")

    xml = _filtrar_xml(respostas)
    marca("filtro drive + nós órfãos")

    with tempfile.TemporaryDirectory(prefix="tonton-osm-") as pasta:
        arq = Path(pasta) / "api.osm"
        arq.write_bytes(xml)
        G = ox.graph_from_xml(arq, simplify=False, retain_all=True)  # recorte e simplificação abaixo, na ordem do osmnx
    marca("graph_from_xml")

    G = ox.truncate.truncate_graph_polygon(G, buffer)
    G = ox.truncate.largest_component(G, strongly=False)
    marca("recorte pelo buffer + componente")
    G_buf = ox.simplification.simplify_graph(G)
    marca("simplificação")
    G = ox.truncate.truncate_graph_polygon(G_buf, poligono)
    G = ox.truncate.largest_component(G, strongly=False)
    nx_spn = ox.stats.count_streets_per_node(G_buf, nodes=G.nodes)
    for no, n in nx_spn.items():
        G.nodes[no]["street_count"] = n
    marca("recorte pelo polígono + componente + street_count")
    G.graph["fonte"] = "api-osm"
    return G


def tabelas(G):
    """Tabela de vértices (y=latitude, x=longitude) e de arestas (nome, comprimento, highway, maxspeed)."""
    return ox.graph_to_gdfs(G)
