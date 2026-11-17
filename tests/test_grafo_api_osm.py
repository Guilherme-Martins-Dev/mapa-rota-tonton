"""Fonte alternativa (API do OSM v0.6) do grafo. Tudo sem rede: requests.get, geocode e graph_from_place falsos."""
import logging
import xml.etree.ElementTree as ET

import networkx as nx
import osmnx as ox
import pytest
import requests
from osmnx import _overpass
from osmnx._errors import ResponseStatusCodeError
from shapely.geometry import LineString, box

from tonton import grafo

LUGAR = "Lugar Falso, Cidade"


@pytest.fixture(autouse=True)
def cache_real_intacto():
    antes = sorted(p.name for p in grafo.CACHE.glob("*"))
    yield
    assert sorted(p.name for p in grafo.CACHE.glob("*")) == antes, "o teste mexeu no cache/ real"


@pytest.fixture(autouse=True)
def pausas(monkeypatch):
    """Silencia a pausa entre GETs (os testes não esperam de verdade) e guarda as que foram pedidas."""
    pedidas = []
    monkeypatch.setattr(grafo.time, "sleep", pedidas.append)
    return pedidas


# ---------------------------------------------------------------- ajudantes
def _osm(nos, ways):
    """nos: {id: (lat, lon)}; ways: {id: (lista_de_nos, {tags})} -> bytes de um XML OSM minúsculo."""
    raiz = ET.Element("osm", {"version": "0.6"})
    for i, (lat, lon) in nos.items():
        ET.SubElement(raiz, "node", {"id": str(i), "lat": str(lat), "lon": str(lon)})
    for i, (refs, tags) in ways.items():
        w = ET.SubElement(raiz, "way", {"id": str(i)})
        for r in refs:
            ET.SubElement(w, "nd", {"ref": str(r)})
        for k, v in tags.items():
            ET.SubElement(w, "tag", {"k": k, "v": v})
    return ET.tostring(raiz, encoding="utf-8", xml_declaration=True)


def _ids(xml, tag):
    return sorted(int(e.get("id")) for e in ET.fromstring(xml).iter(tag))


class Resp:
    def __init__(self, status=200, content=b"<osm/>", text=""):
        self.status_code, self.content, self.text = status, content, text

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"{self.status_code} erro", response=self)


@pytest.fixture
def get_falso(monkeypatch):
    """Registra os GETs; `resposta(params)` devolve a Resp (padrão: 200 com <osm/>)."""
    class Falso:
        chamadas = []
        resposta = staticmethod(lambda params: Resp())

        def __call__(self, url, params=None, headers=None, timeout=None, **kw):
            self.chamadas.append({"url": url, "params": params, "headers": headers, "timeout": timeout})
            return self.resposta(params)

    falso = Falso()
    falso.chamadas = []
    monkeypatch.setattr(grafo.requests, "get", falso)
    return falso


REGRAS = None


def _carro(**tags):
    global REGRAS
    if REGRAS is None:
        REGRAS = grafo._regras_drive()
    return grafo._via_de_carro(tags, REGRAS)


# ---------------------------------------------------------------- _via_de_carro
@pytest.mark.parametrize("tipo", ["residential", "primary", "tertiary", "unclassified", "secondary", "trunk",
                                  "primary_link", "living_street"])
def test_via_de_carro_aceita_tipos_de_carro(tipo):
    assert _carro(highway=tipo)


@pytest.mark.parametrize("tipo", ["footway", "cycleway", "path", "pedestrian", "steps", "track", "construction",
                                  "bridleway", "proposed", "platform"])
def test_via_de_carro_rejeita_tipos_sem_carro(tipo):
    assert not _carro(highway=tipo)


def test_via_de_carro_service_e_rejeitado_como_no_osmnx_drive():
    # No osmnx 2.1.2 o filtro "drive" exclui highway=service (nao so os subtipos): a fonte alternativa segue igual.
    assert "service|services" in _overpass._get_network_filter("drive")
    assert not _carro(highway="service")
    assert not _carro(highway="service", service="parking_aisle")


@pytest.mark.parametrize("tags", [
    {"highway": "residential", "area": "yes"},
    {"highway": "residential", "motor_vehicle": "no"},
    {"highway": "residential", "motorcar": "no"},
    {"highway": "residential", "access": "private"},
    {"highway": "residential", "service": "alley"},
    {"highway": "residential", "service": "driveway"},
    {"highway": "residential", "service": "emergency_access"},
    {"highway": "residential", "service": "parking"},
    {"highway": "residential", "service": "parking_aisle"},
    {"highway": "residential", "service": "private"},
])
def test_via_de_carro_rejeita_por_tags_de_exclusao(tags):
    assert not _carro(**tags)


def test_via_de_carro_sem_highway_rejeita():
    assert not _carro(building="yes")
    assert not _carro()


def test_via_de_carro_tag_ausente_passa_nos_negativos():
    assert _carro(highway="residential")  # sem area/access/motor_vehicle/motorcar/service
    assert _carro(highway="residential", motor_vehicle="yes", area="no", service="spur")


def test_regras_acompanham_o_filtro_drive_da_versao_instalada_do_osmnx():
    """Quebra se o osmnx mudar o filtro `drive`: as exclusoes lidas tem que ser exatamente as do texto."""
    filtro = _overpass._get_network_filter("drive")
    esperado = [(c, p or None) for c, p in __import__("re").findall(r'\["([^"]+)"(?:!~"([^"]*)")?\]', filtro)]
    lidas = [(c, p.pattern if p else None) for c, p in grafo._regras_drive()]
    assert lidas == esperado
    assert lidas[0] == ("highway", None)
    # cada valor listado nas regex e rejeitado; cada chave negativa do filtro esta representada
    for chave, padrao in lidas:
        if padrao is None:
            continue
        for valor in padrao.split("|"):
            assert not grafo._via_de_carro({"highway": "residential", chave: valor} if chave != "highway"
                                           else {"highway": valor}, grafo._regras_drive()), (chave, valor)
    assert {c for c, p in lidas if p} == {"area", "access", "highway", "motor_vehicle", "motorcar", "service"}


def test_regras_drive_formato_inesperado_levanta(monkeypatch):
    monkeypatch.setattr(_overpass, "_get_network_filter", lambda t: '["highway"]')
    with pytest.raises(RuntimeError, match="inesperado"):
        grafo._regras_drive()


# ---------------------------------------------------------------- _filtrar_xml
NOS = {1: (-3.835, -38.498), 2: (-3.835, -38.495), 3: (-3.832, -38.495), 4: (-3.836, -38.490),
       5: (-3.837, -38.489), 6: (-3.900, -38.400)}


def test_filtrar_xml_mantem_so_vias_de_carro_e_seus_nos():
    xml = _osm(NOS, {
        10: ([1, 2], {"highway": "residential"}),
        11: ([2, 3], {"highway": "footway"}),
        12: ([4, 5], {"building": "yes"}),
    })
    saida = grafo._filtrar_xml([xml])
    assert _ids(saida, "way") == [10]
    assert _ids(saida, "node") == [1, 2]  # 3, 4, 5, 6 sao orfaos / de vias descartadas


def test_filtrar_xml_une_respostas_sem_duplicar_ids():
    a = _osm({1: NOS[1], 2: NOS[2]}, {10: ([1, 2], {"highway": "residential"})})
    b = _osm({2: NOS[2], 3: NOS[3]}, {10: ([1, 2], {"highway": "residential"}),
                                      11: ([2, 3], {"highway": "tertiary"})})
    saida = grafo._filtrar_xml([a, b])
    assert _ids(saida, "node") == [1, 2, 3]
    assert _ids(saida, "way") == [10, 11]
    assert len(list(ET.fromstring(saida).iter("node"))) == 3
    assert len(list(ET.fromstring(saida).iter("way"))) == 2


def test_filtrar_xml_vazio_ou_sem_vias_de_carro():
    saida = grafo._filtrar_xml([_osm(NOS, {1: ([1, 2], {"highway": "path"})}), b"<osm/>"])
    assert _ids(saida, "node") == [] and _ids(saida, "way") == []


def test_filtrar_xml_resultado_e_aceito_pelo_osmnx(tmp_path):
    xml = _osm(NOS, {
        10: ([1, 2], {"highway": "residential", "name": "Rua Dupla"}),  # mao dupla
        11: ([2, 3], {"highway": "primary", "oneway": "yes", "name": "Avenida Unica"}),  # mao unica
        12: ([2, 4], {"highway": "cycleway"}),
        13: ([4, 5], {"building": "yes"}),
    })
    arq = tmp_path / "x.osm"
    arq.write_bytes(grafo._filtrar_xml([xml]))
    G = ox.graph_from_xml(arq, simplify=False, retain_all=True)

    assert isinstance(G, nx.MultiDiGraph)
    assert set(G.nodes) == {1, 2, 3}
    assert sorted(G.edges()) == [(1, 2), (2, 1), (2, 3)]  # dupla = 2 arestas; oneway = 1 so
    assert not G.has_edge(3, 2)
    assert all(d["length"] > 0 for *_, d in G.edges(data=True))


# ---------------------------------------------------------------- _baixar_bbox
def _area_do_bbox(params):
    o, s, l, n = (float(v) for v in params["bbox"].split(","))
    return (l - o) * (n - s)


def test_baixar_bbox_200_faz_um_get(get_falso):
    get_falso.resposta = lambda p: Resp(200, b"<osm>a</osm>")
    tempos = {}
    r = grafo._baixar_bbox(-38.5, -3.9, -38.4, -3.8, tempos)
    assert r == [b"<osm>a</osm>"]
    assert len(get_falso.chamadas) == 1
    assert tempos["pedidos GET"] == 1
    assert get_falso.chamadas[0]["url"] == grafo.URL_API_OSM
    assert get_falso.chamadas[0]["params"] == {"bbox": "-38.5,-3.9,-38.4,-3.8"}


def test_baixar_bbox_400_divide_em_4_quartos_e_une(get_falso):
    area = 0.1 * 0.1
    get_falso.resposta = lambda p: Resp(400, text="too many nodes") if _area_do_bbox(p) > area / 2 else Resp(
        200, b"<osm/>")
    tempos = {}
    r = grafo._baixar_bbox(-38.5, -3.9, -38.4, -3.8, tempos)
    assert len(r) == 4
    assert len(get_falso.chamadas) == 5 and tempos["pedidos GET"] == 5
    quartos = {p["params"]["bbox"] for p in get_falso.chamadas[1:]}
    assert len(quartos) == 4
    for q in quartos:
        assert _area_do_bbox({"bbox": q}) == pytest.approx(area / 4)


def test_baixar_bbox_pausa_so_antes_dos_pedidos_filhos(get_falso, pausas):
    area = 0.1 * 0.1
    get_falso.resposta = lambda p: Resp(400, text="too many nodes") if _area_do_bbox(p) > area / 2 else Resp(
        200, b"<osm/>")
    grafo._baixar_bbox(-38.5, -3.9, -38.4, -3.8, {})
    assert len(get_falso.chamadas) == 5
    assert pausas == [grafo.PAUSA_ENTRE_GETS_S] * 4  # 1 pedido raiz sem pausa + 4 filhos com pausa


def test_baixar_bbox_200_direto_nao_pausa(get_falso, pausas):
    get_falso.resposta = lambda p: Resp(200, b"<osm/>")
    grafo._baixar_bbox(-38.5, -3.9, -38.4, -3.8, {})
    assert pausas == []


def test_pior_caso_de_pedidos_declarado_bate_com_a_constante():
    # 1 + 4 + 16 + 64 = 85 quando a API recusa tudo até o último nível e aceita só no nível máximo
    assert sum(4 ** n for n in range(grafo.MAX_NIVEL_BISSECAO + 1)) == 85


def test_baixar_bbox_divide_recursivamente_e_para_quando_aceita(get_falso):
    # recusa tudo acima de 1/16 da area: nivel 0 e nivel 1 recusam; nivel 2 aceita
    area = 0.1 * 0.1
    get_falso.resposta = lambda p: Resp(400) if _area_do_bbox(p) > area / 16 * 1.01 else Resp(200, b"<osm/>")
    tempos = {}
    r = grafo._baixar_bbox(-38.5, -3.9, -38.4, -3.8, tempos)
    assert len(r) == 16
    assert tempos["pedidos GET"] == 1 + 4 + 16 == len(get_falso.chamadas)


def test_baixar_bbox_so_divide_o_quarto_recusado(get_falso):
    primeiro = {"visto": False}

    def resposta(p):
        if _area_do_bbox(p) > 0.0026:  # raiz recusa
            return Resp(400)
        if not primeiro["visto"]:  # so o 1o quarto e recusado
            primeiro["visto"] = True
            return Resp(400)
        return Resp(200, b"<osm/>")

    get_falso.resposta = resposta
    r = grafo._baixar_bbox(-38.5, -3.9, -38.4, -3.8, {})
    assert len(r) == 3 + 4
    assert len(get_falso.chamadas) == 1 + 1 + 4 + 3


def test_baixar_bbox_400_no_nivel_maximo_levanta_valueerror_claro(get_falso):
    get_falso.resposta = lambda p: Resp(400, text="You requested too many nodes")
    with pytest.raises(ValueError, match="400") as exc:
        grafo._baixar_bbox(-38.5, -3.9, -38.4, -3.8, {}, max_nivel=2)
    assert "too many nodes" in str(exc.value)
    assert not isinstance(exc.value, ResponseStatusCodeError)  # o fallback nao pode engolir isto
    assert len(get_falso.chamadas) == 3  # desce 0 -> 1 -> 2 e desiste no primeiro


def test_baixar_bbox_max_nivel_zero_nao_divide(get_falso):
    get_falso.resposta = lambda p: Resp(400, text="x")
    with pytest.raises(ValueError):
        grafo._baixar_bbox(-38.5, -3.9, -38.4, -3.8, {}, max_nivel=0)
    assert len(get_falso.chamadas) == 1


@pytest.mark.parametrize("status", [500, 502, 429, 503, 404])
def test_baixar_bbox_outros_status_levantam_erro_de_rede_sem_dividir(get_falso, status):
    get_falso.resposta = lambda p: Resp(status)
    with pytest.raises(requests.exceptions.RequestException):
        grafo._baixar_bbox(-38.5, -3.9, -38.4, -3.8, {})
    assert len(get_falso.chamadas) == 1
    assert issubclass(requests.exceptions.HTTPError, grafo.ERROS_DE_REDE)


def test_baixar_bbox_envia_user_agent_e_timeout_em_todos_os_gets(get_falso):
    get_falso.resposta = lambda p: Resp(400) if _area_do_bbox(p) > 0.003 else Resp(200, b"<osm/>")
    grafo._baixar_bbox(-38.5, -3.9, -38.4, -3.8, {})
    assert len(get_falso.chamadas) > 1
    for c in get_falso.chamadas:
        assert c["headers"] == {"User-Agent": grafo.USER_AGENT}
        assert c["timeout"] is not None and c["timeout"] > 0
    assert "tonton" in grafo.USER_AGENT.lower()


# ---------------------------------------------------------------- baixar_via_api_osm
POLIGONO = box(-38.500, -3.840, -38.490, -3.830)


@pytest.fixture
def geocode_falso(monkeypatch):
    import geopandas as gpd

    chamadas = []

    def falso(query, **kw):
        chamadas.append(query)
        return gpd.GeoDataFrame({"geometry": [POLIGONO]}, crs="EPSG:4326")

    monkeypatch.setattr(grafo.ox.geocoder, "geocode_to_gdf", falso)
    return chamadas


# 1-2-3 em linha, 4 sai do 2; 5 esta fora do poligono (mas dentro do buffer de 500 m); footway e predio extras
NOS_API = {1: (-3.835, -38.498), 2: (-3.835, -38.495), 3: (-3.835, -38.492), 4: (-3.832, -38.495),
           5: (-3.835, -38.488), 6: (-3.838, -38.497), 7: (-3.838, -38.496)}
XML_API = _osm(NOS_API, {
    10: ([1, 2], {"highway": "residential", "name": "Rua A"}),
    11: ([2, 3, 5], {"highway": "primary", "oneway": "yes", "name": "Avenida B"}),
    12: ([2, 4], {"highway": "tertiary"}),
    13: ([6, 7], {"highway": "footway"}),
    14: ([6, 7, 1], {"building": "yes"}),
})


def test_baixar_via_api_osm_fonte_recorte_e_contadores(get_falso, geocode_falso):
    get_falso.resposta = lambda p: Resp(200, XML_API)
    tempos = {}
    G = grafo.baixar_via_api_osm(LUGAR, tempos)

    assert geocode_falso == [LUGAR]
    assert G.graph["fonte"] == "api-osm"
    assert G.is_directed() and G.is_multigraph()
    assert 5 not in G.nodes  # fora do poligono
    assert 6 not in G.nodes and 7 not in G.nodes  # footway/predio filtrados
    assert {1, 2, 4} <= set(G.nodes)
    assert all("street_count" in d for _, d in G.nodes(data=True))
    assert tempos["pedidos GET"] == 1 and tempos["pedidos aceitos"] == 1
    assert get_falso.chamadas[0]["headers"]["User-Agent"] == grafo.USER_AGENT
    # bbox enviado = poligono + ~500 m
    o, s, l, n = (float(v) for v in get_falso.chamadas[0]["params"]["bbox"].split(","))
    assert o < -38.500 and l > -38.490 and s < -3.840 and n > -3.830
    assert (l - o) * (n - s) < grafo.LIMITE_AREA_API


def test_baixar_via_api_osm_com_bissecao_conta_pedidos(get_falso, geocode_falso):
    get_falso.resposta = lambda p: Resp(400) if _area_do_bbox(p) > 0.0001 else Resp(200, XML_API)
    tempos = {}
    G = grafo.baixar_via_api_osm(LUGAR, tempos)
    assert tempos["pedidos GET"] == len(get_falso.chamadas) == 5
    assert tempos["pedidos aceitos"] == 4
    assert 1 in G.nodes and 5 not in G.nodes  # mesmos ids repetidos nas 4 respostas nao duplicam nada


def test_baixar_via_api_osm_bbox_acima_do_limite_levanta_antes_de_qualquer_get(get_falso, monkeypatch):
    import geopandas as gpd
    grande = box(-39.0, -4.0, -38.0, -3.0)  # 1 grau²
    monkeypatch.setattr(grafo.ox.geocoder, "geocode_to_gdf",
                        lambda q, **kw: gpd.GeoDataFrame({"geometry": [grande]}, crs="EPSG:4326"))
    with pytest.raises(ValueError, match="0.25"):
        grafo.baixar_via_api_osm(LUGAR)
    assert get_falso.chamadas == []


def test_baixar_via_api_osm_status_500_vira_erro_de_rede(get_falso, geocode_falso):
    get_falso.resposta = lambda p: Resp(500)
    with pytest.raises(grafo.ERROS_DE_REDE):
        grafo.baixar_via_api_osm(LUGAR)
    assert len(get_falso.chamadas) == 1


# ---------------------------------------------------------------- carregar_grafo: Overpass -> API
def _bruto():
    G = nx.MultiDiGraph(crs="EPSG:4326")
    G.add_node(1, x=-38.500, y=-3.800)
    G.add_node(2, x=-38.490, y=-3.800)
    G.add_edge(1, 2, osmid=10, length=1000.0, highway="primary", name="Av", oneway=True, reversed=False,
               geometry=LineString([(-38.500, -3.800), (-38.490, -3.800)]))
    return G


def _api_falsa(chamadas):
    def f(lugar, tempos=None):
        chamadas.append(lugar)
        G = _bruto()
        G.graph["fonte"] = "api-osm"
        return G
    return f


def test_overpass_ok_nao_chama_a_api(monkeypatch, tmp_path):
    monkeypatch.setattr(grafo.ox, "graph_from_place", lambda lugar, network_type: _bruto())
    api = []
    monkeypatch.setattr(grafo, "baixar_via_api_osm", _api_falsa(api))
    G = grafo.carregar_grafo(LUGAR, pasta=tmp_path)
    assert api == []
    assert G.graph["fonte"] == "overpass"
    assert grafo.arquivo_cache(LUGAR, tmp_path).is_file()


@pytest.mark.parametrize("erro", [
    requests.exceptions.ConnectTimeout("timeout"),
    requests.exceptions.ConnectionError("sem rede"),
    ResponseStatusCodeError("Server returned HTTP status 504"),
], ids=["ConnectTimeout", "ConnectionError", "ResponseStatusCodeError"])
def test_overpass_falha_de_rede_cai_na_api_loga_e_grava(monkeypatch, tmp_path, caplog, erro):
    def quebra(lugar, network_type):
        raise erro

    monkeypatch.setattr(grafo.ox, "graph_from_place", quebra)
    api = []
    monkeypatch.setattr(grafo, "baixar_via_api_osm", _api_falsa(api))
    with caplog.at_level(logging.WARNING, logger="tonton"):
        G = grafo.carregar_grafo(LUGAR, pasta=tmp_path)

    assert api == [LUGAR]
    assert G.graph["fonte"] == "api-osm"
    avisos = [r for r in caplog.records if r.name == "tonton" and r.levelno == logging.WARNING]
    assert len(avisos) == 1
    assert type(erro).__name__ in avisos[0].getMessage()
    assert grafo.arquivo_cache(LUGAR, tmp_path).is_file()
    assert [p.name for p in tmp_path.iterdir()] == [grafo.arquivo_cache(LUGAR, tmp_path).name]


@pytest.mark.parametrize("erro", [KeyError("chave"), TypeError("bug"), AttributeError("x"), RuntimeError("y")])
def test_erro_de_programacao_no_overpass_propaga_sem_fallback(monkeypatch, tmp_path, erro):
    def quebra(lugar, network_type):
        raise erro

    monkeypatch.setattr(grafo.ox, "graph_from_place", quebra)
    api = []
    monkeypatch.setattr(grafo, "baixar_via_api_osm", _api_falsa(api))
    with pytest.raises(type(erro)):
        grafo.carregar_grafo(LUGAR, pasta=tmp_path)
    assert api == []
    assert list(tmp_path.iterdir()) == []


def test_fonte_sobrevive_ao_ida_e_volta_graphml(monkeypatch, tmp_path):
    monkeypatch.setattr(grafo.ox, "graph_from_place",
                        lambda lugar, network_type: (_ for _ in ()).throw(requests.exceptions.ConnectTimeout("t")))
    monkeypatch.setattr(grafo, "baixar_via_api_osm", _api_falsa([]))
    grafo.carregar_grafo(LUGAR, pasta=tmp_path)

    # 2a chamada: cache valido; nenhuma fonte e consultada e a fonte original continua la
    monkeypatch.setattr(grafo.ox, "graph_from_place", lambda *a, **k: pytest.fail("nao devia baixar"))
    monkeypatch.setattr(grafo, "baixar_via_api_osm", lambda *a, **k: pytest.fail("nao devia baixar"))
    G = grafo.carregar_grafo(LUGAR, pasta=tmp_path)
    assert G.graph["fonte"] == "api-osm"

    # e para a Overpass
    outra = tmp_path / "outra"
    monkeypatch.setattr(grafo.ox, "graph_from_place", lambda lugar, network_type: _bruto())
    grafo.carregar_grafo(LUGAR, pasta=outra)
    monkeypatch.setattr(grafo.ox, "graph_from_place", lambda *a, **k: pytest.fail("nao devia baixar"))
    assert grafo.carregar_grafo(LUGAR, pasta=outra).graph["fonte"] == "overpass"


def test_api_tambem_falha_sobe_a_excecao_e_nao_deixa_arquivo(monkeypatch, tmp_path):
    def overpass(lugar, network_type):
        raise requests.exceptions.ConnectTimeout("overpass fora")

    def api(lugar, tempos=None):
        raise requests.exceptions.ConnectionError("api fora")

    monkeypatch.setattr(grafo.ox, "graph_from_place", overpass)
    monkeypatch.setattr(grafo, "baixar_via_api_osm", api)
    with pytest.raises(requests.exceptions.ConnectionError, match="api fora"):
        grafo.carregar_grafo(LUGAR, pasta=tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_falha_ao_gravar_apaga_o_tmp(monkeypatch, tmp_path):
    monkeypatch.setattr(grafo.ox, "graph_from_place", lambda lugar, network_type: _bruto())

    def quebra(G, caminho):
        caminho.write_text("parcial")
        raise OSError("disco cheio")

    monkeypatch.setattr(grafo.ox, "save_graphml", quebra)
    with pytest.raises(OSError):
        grafo.carregar_grafo(LUGAR, pasta=tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_usar_cache_false_baixa_de_novo_mesmo_com_cache_valido(monkeypatch, tmp_path):
    chamadas = []

    def overpass(lugar, network_type):
        chamadas.append(lugar)
        return _bruto()

    monkeypatch.setattr(grafo.ox, "graph_from_place", overpass)
    grafo.carregar_grafo(LUGAR, pasta=tmp_path)
    grafo.carregar_grafo(LUGAR, pasta=tmp_path)
    assert len(chamadas) == 1
    grafo.carregar_grafo(LUGAR, usar_cache=False, pasta=tmp_path)
    assert len(chamadas) == 2


def test_usar_cache_false_tambem_cai_na_api(monkeypatch, tmp_path):
    grafo.ox.save_graphml(_bruto(), grafo.arquivo_cache(LUGAR, tmp_path))
    monkeypatch.setattr(grafo.ox, "graph_from_place",
                        lambda lugar, network_type: (_ for _ in ()).throw(requests.exceptions.ReadTimeout("t")))
    api = []
    monkeypatch.setattr(grafo, "baixar_via_api_osm", _api_falsa(api))
    G = grafo.carregar_grafo(LUGAR, usar_cache=False, pasta=tmp_path)
    assert api == [LUGAR] and G.graph["fonte"] == "api-osm"


def test_integracao_overpass_fora_api_real_com_xml_falso(monkeypatch, tmp_path, get_falso, geocode_falso):
    """carregar_grafo -> baixar_via_api_osm de verdade (so requests.get/geocode/graph_from_place falsos)."""
    monkeypatch.setattr(grafo.ox, "graph_from_place",
                        lambda lugar, network_type: (_ for _ in ()).throw(requests.exceptions.ConnectTimeout("t")))
    get_falso.resposta = lambda p: Resp(200, XML_API)
    G = grafo.carregar_grafo(LUGAR, pasta=tmp_path)
    assert G.graph["fonte"] == "api-osm"
    assert 5 not in G.nodes
    assert grafo.ox.load_graphml(grafo.arquivo_cache(LUGAR, tmp_path)).graph["fonte"] == "api-osm"
