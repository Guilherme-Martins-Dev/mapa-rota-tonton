import math

import networkx as nx
import pytest
from shapely.geometry import LineString

from tonton import pesos
from tonton.consumo import litros
from tonton.planejador import (
    Criterio,
    Resumo,
    comparar,
    geojson,
    geojson_colecao,
    planejar,
    planejar_alternativas,
    preparar_grafo,
    resolver_ponto,
    vertice_mais_proximo,
)
from tonton.rotas import Rota, RotaInexistente


def _grafo_tres_vias():
    """s->t por tres vias (maxspeed define a velocidade, sem TomTom).

    d: 3 km a 20 km/h (curta, lenta); f: 5 km a 120 km/h (rapida); e: 4 km a 65 km/h (economica).
    Ha ainda uma aresta paralela pior s->d (5 km a 20 km/h), que nunca deve ser escolhida.
    """
    G = nx.MultiDiGraph()
    G.add_node("s", x=-38.500, y=-3.800)
    G.add_node("t", x=-38.460, y=-3.800)
    G.add_node("d", x=-38.480, y=-3.790)
    G.add_node("f", x=-38.480, y=-3.800)
    G.add_node("e", x=-38.480, y=-3.810)
    vias = {"d": (3000.0, "20", "Rua Direta"), "f": (5000.0, "120", ["Rodovia Rapida", "CE-040"]),
            "e": (4000.0, "65", None)}
    for meio, (comp, ms, nome) in vias.items():
        atributos = {"length": comp / 2, "maxspeed": ms}
        if nome is not None:
            atributos["name"] = nome
        G.add_edge("s", meio, **atributos)
        G.add_edge(meio, "t", **atributos)
    G.add_edge("s", "d", length=5000.0, maxspeed="20")  # paralela pior
    return preparar_grafo(G)


def _soma(G, resumo, atributo):
    return sum(G[u][v][k][atributo] for u, v, k in resumo.rota.arestas)


# ---------- planejar ----------

def test_tres_criterios_escolhem_vias_diferentes():
    G = _grafo_tres_vias()
    r = planejar(G, "s", "t")
    assert set(r) == set(Criterio)
    assert r[Criterio.DISTANCIA].rota.vertices == ["s", "d", "t"]
    assert r[Criterio.TEMPO].rota.vertices == ["s", "f", "t"]
    assert r[Criterio.CONSUMO].rota.vertices == ["s", "e", "t"]
    for c, resumo in r.items():
        assert isinstance(resumo, Resumo)
        assert resumo.criterio is c
        assert isinstance(resumo.rota, Rota)


def test_totais_somados_sobre_as_arestas_escolhidas():
    G = _grafo_tres_vias()
    r = planejar(G, "s", "t")
    esperado = {  # (metros, km/h) de cada via
        Criterio.DISTANCIA: (3000, 20), Criterio.TEMPO: (5000, 120), Criterio.CONSUMO: (4000, 65),
    }
    for c, (metros, v) in esperado.items():
        assert r[c].distancia_km == pytest.approx(metros / 1000)
        assert r[c].tempo_min == pytest.approx(pesos.tempo(metros, v) / 60)
        assert r[c].litros == pytest.approx(litros(metros, v))
    # comparacao justa: cada criterio e o melhor na sua propria coluna
    assert r[Criterio.DISTANCIA].distancia_km == min(x.distancia_km for x in r.values())
    assert r[Criterio.TEMPO].tempo_min == min(x.tempo_min for x in r.values())
    assert r[Criterio.CONSUMO].litros == min(x.litros for x in r.values())


def test_totais_coincidem_com_soma_das_arestas_do_grafo():
    G = _grafo_tres_vias()
    for resumo in planejar(G, "s", "t").values():
        assert resumo.distancia_km * 1000 == pytest.approx(_soma(G, resumo, "length"))
        assert resumo.tempo_min * 60 == pytest.approx(_soma(G, resumo, "t_atual"))
        assert resumo.litros == pytest.approx(_soma(G, resumo, "litros"))


def test_aresta_paralela_nao_escolhida_nao_entra_na_soma():
    G = _grafo_tres_vias()
    resumo = planejar(G, "s", "t", Criterio.DISTANCIA)[Criterio.DISTANCIA]
    assert resumo.rota.arestas[0] == ("s", "d", 0)  # a de 1500 m, nao a paralela de 5000 m
    assert resumo.distancia_km == pytest.approx(3.0)


def test_paralela_melhor_e_a_usada_nos_totais():
    G = nx.MultiDiGraph()
    G.add_node("a", x=-38.5, y=-3.8)
    G.add_node("b", x=-38.49, y=-3.8)
    G.add_edge("a", "b", length=2000.0, maxspeed="30")
    k = G.add_edge("a", "b", length=1000.0, maxspeed="60")
    preparar_grafo(G)
    for c, resumo in planejar(G, "a", "b").items():
        assert resumo.rota.arestas == [("a", "b", k)], c
        assert resumo.distancia_km == pytest.approx(1.0)
        assert resumo.tempo_min == pytest.approx(pesos.tempo(1000, 60) / 60)


def test_criterio_unico_devolve_so_um():
    G = _grafo_tres_vias()
    for c in Criterio:
        r = planejar(G, "s", "t", c)
        assert list(r) == [c]
        assert r[c].criterio is c


def test_mao_unica_e_destino_inalcancavel():
    G = _grafo_tres_vias()
    assert planejar(G, "s", "t", Criterio.TEMPO)
    with pytest.raises(RotaInexistente):
        planejar(G, "t", "s")  # so existe s->t
    G.add_node("ilha", x=-38.0, y=-3.0)
    with pytest.raises(RotaInexistente):
        planejar(G, "s", "ilha")


def test_origem_igual_destino_totais_zero():
    G = _grafo_tres_vias()
    for resumo in planejar(G, "s", "s").values():
        assert resumo.rota.vertices == ["s"]
        assert resumo.distancia_km == 0 and resumo.tempo_min == 0 and resumo.litros == 0


def test_aresta_sem_peso_finito_levanta_valueerror_citando_a_aresta():
    G = _grafo_tres_vias()
    G["s"]["d"][0]["t_atual"] = math.inf  # distancia ainda escolhe essa aresta, mas o tempo nao soma
    with pytest.raises(ValueError, match=r"t_atual") as exc:
        planejar(G, "s", "t", Criterio.DISTANCIA)
    assert "('s', 'd', 0)" in str(exc.value)


def test_aresta_com_litros_none_levanta_valueerror():
    G = _grafo_tres_vias()
    G["s"]["d"][0]["litros"] = None
    with pytest.raises(ValueError, match="litros"):
        planejar(G, "s", "t", Criterio.DISTANCIA)


def test_velocidade_zero_na_tomtom_cai_no_fallback_e_planeja():
    G = nx.MultiDiGraph()
    G.add_node("a", x=-38.5, y=-3.8)
    G.add_node("b", x=-38.49, y=-3.8)
    G.add_edge("a", "b", length=1000.0, highway="primary", maxspeed="50")
    preparar_grafo(G, consultar=lambda lat, lon: {"currentSpeed": 0, "freeFlowSpeed": 50})
    r = planejar(G, "a", "b")[Criterio.TEMPO]
    assert math.isfinite(r.tempo_min) and math.isfinite(r.litros)
    assert r.tempo_min == pytest.approx(pesos.tempo(1000, 50) / 60)


def test_preparar_grafo_com_consultar_usa_transito():
    G = nx.MultiDiGraph()
    G.add_node("a", x=-38.5, y=-3.8)
    G.add_node("b", x=-38.49, y=-3.8)
    G.add_edge("a", "b", length=1000.0, highway="primary", maxspeed="60")
    chamadas = []

    def consultar(lat, lon):
        chamadas.append((lat, lon))
        return {"currentSpeed": 20, "freeFlowSpeed": 60}

    assert preparar_grafo(G, consultar) is G
    assert len(chamadas) == 1
    d = G["a"]["b"][0]
    assert d["v_atual"] == 20 and d["v_livre"] == 60
    assert d["litros"] == pytest.approx(litros(1000, 20))


# ---------- vertice_mais_proximo / resolver_ponto ----------

def test_vertice_mais_proximo_coordenada_exata_e_proxima():
    G = _grafo_tres_vias()
    assert vertice_mais_proximo(G, -3.800, -38.500) == "s"
    assert vertice_mais_proximo(G, -3.790, -38.480) == "d"
    assert vertice_mais_proximo(G, -3.8001, -38.4599) == "t"
    assert vertice_mais_proximo(G, -3.8095, -38.4801) == "e"


def test_vertice_mais_proximo_usa_lat_lon_nao_x_y_invertidos():
    G = nx.MultiDiGraph()
    G.add_node("a", x=-38.5, y=-3.8)  # lon, lat
    G.add_node("b", x=-3.8, y=-38.5)  # armadilha invertida
    assert vertice_mais_proximo(G, -3.8, -38.5) == "a"


def test_vertice_mais_proximo_grafo_vazio():
    with pytest.raises(ValueError):
        vertice_mais_proximo(nx.MultiDiGraph(), 0, 0)


def test_resolver_ponto_lat_lon_valido_e_com_espacos():
    G = _grafo_tres_vias()
    assert resolver_ponto(G, "-3.8,-38.5") == "s"
    assert resolver_ponto(G, "  -3.8 ,   -38.46  ") == "t"
    assert resolver_ponto(G, "-3.79, -38.48") == "d"


@pytest.mark.parametrize("texto", ["91,0", "-91,0", "0,181", "0,-181"])
def test_resolver_ponto_fora_do_intervalo(texto):
    with pytest.raises(ValueError, match="intervalo"):
        resolver_ponto(_grafo_tres_vias(), texto)


def test_resolver_ponto_nome_de_rua_com_acento_e_caixa_diferentes():
    G = nx.MultiDiGraph()
    G.add_node(1, x=-38.5, y=-3.8)
    G.add_node(2, x=-38.49, y=-3.8)
    G.add_edge(1, 2, length=100.0, name="Avenida Água Fria")
    assert resolver_ponto(G, "agua FRIA") == 2  # cruzamento seguinte
    assert resolver_ponto(G, "ÁGUA fria") == 2


def test_resolver_ponto_name_em_lista_e_trecho_sem_name():
    G = _grafo_tres_vias()
    assert resolver_ponto(G, "rodovia rapida") == "f"  # primeiro trecho achado: s->f
    assert resolver_ponto(G, "ce-040") == "f"          # casa o 2o nome da lista
    # a via "e" nao tem name: nao quebra a busca nem e achada
    with pytest.raises(ValueError):
        resolver_ponto(G, "economica")


def test_resolver_ponto_rua_inexistente():
    with pytest.raises(ValueError, match="Rua Que Nao Existe"):
        resolver_ponto(_grafo_tres_vias(), "Rua Que Nao Existe")


# ---------- comparar ----------

def test_comparar_uma_linha_por_criterio_e_marca_o_melhor():
    G = _grafo_tres_vias()
    r = planejar(G, "s", "t")
    linhas = comparar(r).splitlines()
    assert len(linhas) == 1 + 3 + 1  # cabecalho, 3 criterios, legenda
    por_nome = {n: l for n in ("menor distância", "menor tempo", "menor consumo") for l in linhas if l.startswith(n)}
    assert len(por_nome) == 3
    # cada criterio vence exatamente a sua coluna (um '*' por linha)
    assert por_nome["menor distância"].count("*") == 1
    assert por_nome["menor tempo"].count("*") == 1
    assert por_nome["menor consumo"].count("*") == 1
    assert "km*" in por_nome["menor distância"]
    assert "min*" in por_nome["menor tempo"]
    assert "L*" in por_nome["menor consumo"]
    assert "* = melhor" in linhas[-1]


def test_comparar_empate_marca_todos():
    G = nx.MultiDiGraph()
    G.add_node("a", x=-38.5, y=-3.8)
    G.add_node("b", x=-38.49, y=-3.8)
    G.add_edge("a", "b", length=1000.0, maxspeed="50")
    preparar_grafo(G)
    linhas = comparar(planejar(G, "a", "b")).splitlines()
    corpo = linhas[1:4]
    assert len(corpo) == 3
    for l in corpo:
        assert l.count("*") == 3  # km, min e L marcados em todas


def test_comparar_um_criterio_e_vazio():
    G = _grafo_tres_vias()
    linhas = comparar(planejar(G, "s", "t", Criterio.TEMPO)).splitlines()
    assert len(linhas) == 3
    assert linhas[1].count("*") == 3
    assert comparar({}) == ""


# ---------- geojson ----------

def test_geojson_ordem_lon_lat_sem_geometry_e_properties():
    G = _grafo_tres_vias()
    resumo = planejar(G, "s", "t", Criterio.TEMPO)[Criterio.TEMPO]
    f = geojson(G, resumo)
    assert f["type"] == "Feature"
    assert f["geometry"]["type"] == "LineString"
    assert f["geometry"]["coordinates"] == [[-38.500, -3.800], [-38.480, -3.800], [-38.460, -3.800]]
    p = f["properties"]
    assert p["criterio"] == "tempo"
    assert p["distancia_km"] == pytest.approx(resumo.distancia_km)
    assert p["tempo_min"] == pytest.approx(resumo.tempo_min)
    assert p["litros"] == pytest.approx(resumo.litros)


def test_geojson_criterio_em_minusculas_para_todos():
    G = _grafo_tres_vias()
    nomes = {geojson(G, r)["properties"]["criterio"] for r in planejar(G, "s", "t").values()}
    assert nomes == {"distancia", "tempo", "consumo"}


def test_geojson_usa_geometry_da_aresta_sem_duplicar_juncao():
    G = nx.MultiDiGraph()
    G.add_node("a", x=0.0, y=0.0)
    G.add_node("b", x=2.0, y=0.0)
    G.add_node("c", x=4.0, y=0.0)
    G.add_edge("a", "b", length=100.0, maxspeed="30", geometry=LineString([(0, 0), (1, 0.5), (2, 0)]))
    G.add_edge("b", "c", length=100.0, maxspeed="30", geometry=LineString([(2, 0), (3, -0.5), (4, 0)]))
    preparar_grafo(G)
    f = geojson(G, planejar(G, "a", "c", Criterio.DISTANCIA)[Criterio.DISTANCIA])
    assert f["geometry"]["coordinates"] == [[0, 0], [1, 0.5], [2, 0], [3, -0.5], [4, 0]]


def test_geojson_geometria_invertida_sai_de_u_para_v():
    G = nx.MultiDiGraph()
    G.add_node("a", x=0.0, y=0.0)
    G.add_node("b", x=2.0, y=0.0)
    G.add_node("c", x=4.0, y=0.0)
    # geometria guardada de b para a (invertida em relação a a->b)
    G.add_edge("a", "b", length=100.0, maxspeed="30", geometry=LineString([(2, 0), (1, 0.5), (0, 0)]))
    G.add_edge("b", "c", length=100.0, maxspeed="30", geometry=LineString([(2, 0), (3, -0.5), (4, 0)]))
    preparar_grafo(G)
    f = geojson(G, planejar(G, "a", "c", Criterio.DISTANCIA)[Criterio.DISTANCIA])
    assert f["geometry"]["coordinates"] == [[0, 0], [1, 0.5], [2, 0], [3, -0.5], [4, 0]]


def test_geojson_mistura_com_e_sem_geometry():
    G = nx.MultiDiGraph()
    G.add_node("a", x=0.0, y=0.0)
    G.add_node("b", x=2.0, y=0.0)
    G.add_node("c", x=4.0, y=1.0)
    G.add_edge("a", "b", length=100.0, maxspeed="30", geometry=LineString([(0, 0), (1, 0.5), (2, 0)]))
    G.add_edge("b", "c", length=100.0, maxspeed="30")
    preparar_grafo(G)
    f = geojson(G, planejar(G, "a", "c", Criterio.DISTANCIA)[Criterio.DISTANCIA])
    assert f["geometry"]["coordinates"] == [[0, 0], [1, 0.5], [2, 0], [4, 1]]


def test_geojson_origem_igual_destino_repete_o_ponto():
    G = _grafo_tres_vias()
    f = geojson(G, planejar(G, "s", "s", Criterio.DISTANCIA)[Criterio.DISTANCIA])
    assert f["geometry"]["coordinates"] == [[-38.5, -3.8], [-38.5, -3.8]]
    assert f["properties"]["distancia_km"] == 0


# ---------- alternativas ----------

def test_planejar_alternativas_ordem_e_totais_sobre_as_arestas():
    G = _grafo_tres_vias()
    rs = planejar_alternativas(G, "s", "t", Criterio.DISTANCIA, k=3, max_sobreposicao=1.0)
    assert [r.rota.vertices for r in rs] == [["s", "d", "t"], ["s", "e", "t"], ["s", "f", "t"]]
    for r in rs:
        assert isinstance(r, Resumo) and r.criterio is Criterio.DISTANCIA
        assert r.distancia_km == pytest.approx(_soma(G, r, "length") / 1000)
        assert r.tempo_min == pytest.approx(_soma(G, r, "t_atual") / 60)
        assert r.litros == pytest.approx(_soma(G, r, "litros"))
    assert [r.distancia_km for r in rs] == pytest.approx([3.0, 4.0, 5.0])
    # a ótima coincide com planejar
    assert rs[0].rota.vertices == planejar(G, "s", "t", Criterio.DISTANCIA)[Criterio.DISTANCIA].rota.vertices


def test_planejar_alternativas_k_um_e_k_maior_que_caminhos():
    G = _grafo_tres_vias()
    assert len(planejar_alternativas(G, "s", "t", Criterio.TEMPO, k=1)) == 1
    assert len(planejar_alternativas(G, "s", "t", Criterio.TEMPO, k=10, max_sobreposicao=1.0)) == 3


def test_planejar_alternativas_criterios_diferentes_ordenam_diferente():
    G = _grafo_tres_vias()
    assert planejar_alternativas(G, "s", "t", Criterio.TEMPO, k=1)[0].rota.vertices == ["s", "f", "t"]
    assert planejar_alternativas(G, "s", "t", Criterio.CONSUMO, k=1)[0].rota.vertices == ["s", "e", "t"]


def test_planejar_alternativas_peso_nao_finito_no_total():
    G = _grafo_tres_vias()
    G["s"]["d"][0]["t_atual"] = float("nan")  # aresta da rota ótima por distância
    with pytest.raises(ValueError):
        planejar_alternativas(G, "s", "t", Criterio.DISTANCIA, k=2)


def test_planejar_alternativas_inalcancavel_e_k_invalido():
    G = _grafo_tres_vias()
    G.add_node("ilha", x=-38.4, y=-3.8)
    with pytest.raises(RotaInexistente):
        planejar_alternativas(G, "s", "ilha", Criterio.TEMPO, k=3)
    with pytest.raises(ValueError):
        planejar_alternativas(G, "s", "t", Criterio.TEMPO, k=0)
    with pytest.raises(ValueError):
        planejar_alternativas(G, "s", "t", Criterio.TEMPO, k=2, max_sobreposicao=1.5)


def test_geojson_colecao_indice_e_criterio():
    G = _grafo_tres_vias()
    rs = planejar_alternativas(G, "s", "t", Criterio.CONSUMO, k=3, max_sobreposicao=1.0)
    col = geojson_colecao(G, rs)
    assert col["type"] == "FeatureCollection" and len(col["features"]) == 3
    assert [f["properties"]["indice"] for f in col["features"]] == [0, 1, 2]
    for f, r in zip(col["features"], rs):
        assert f["properties"]["criterio"] == "consumo"
        assert f["properties"]["litros"] == r.litros
        assert f["geometry"]["type"] == "LineString"
    assert col["features"][0]["geometry"] == geojson(G, rs[0])["geometry"]
    assert geojson_colecao(G, []) == {"type": "FeatureCollection", "features": []}


def test_comparar_lista_de_alternativas():
    G = _grafo_tres_vias()
    rs = planejar_alternativas(G, "s", "t", Criterio.DISTANCIA, k=3, max_sobreposicao=1.0)
    texto = comparar(rs)
    linhas = texto.splitlines()
    assert len(linhas) == 1 + 3 + 1
    assert linhas[0].startswith("rota")
    assert linhas[1].startswith("ótima") and linhas[2].startswith("alt 1") and linhas[3].startswith("alt 2")
    assert "menor distância" not in texto
    assert "*" in linhas[1]  # a ótima por distância é a menor em km
    assert comparar([]) == ""


def test_comparar_dict_uso_antigo():
    G = _grafo_tres_vias()
    texto = comparar(planejar(G, "s", "t"))
    for rotulo in ("menor distância", "menor tempo", "menor consumo"):
        assert rotulo in texto
    assert texto.splitlines()[0].startswith("critério")
    assert comparar({}) == ""
