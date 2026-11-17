import json

import networkx as nx
import pytest

from tonton import cli
from tonton.planejador import Criterio


def _grafo():
    """s->t por 3 vias; s->f e f->t sao 'primary' (consultaveis na TomTom)."""
    G = nx.MultiDiGraph()
    G.add_node("s", x=-38.500, y=-3.800)
    G.add_node("t", x=-38.460, y=-3.800)
    G.add_node("d", x=-38.480, y=-3.790)
    G.add_node("f", x=-38.480, y=-3.800)
    G.add_node("e", x=-38.480, y=-3.810)
    vias = {"d": (3000.0, "20", "Rua Direta", "residential"), "f": (5000.0, "120", "Avenida Rapida", "primary"),
            "e": (4000.0, "65", None, "residential")}
    for meio, (comp, ms, nome, hw) in vias.items():
        at = {"length": comp / 2, "maxspeed": ms, "highway": hw}
        if nome:
            at["name"] = nome
        G.add_edge("s", meio, **at)
        G.add_edge(meio, "t", **at)
    return G


S, T = "-3.8,-38.5", "-3.8,-38.46"


def _norm(argv):
    """argparse rejeita "--origem -3.8,-38.5" (valor com '-' inicial); usa a forma --opt=valor."""
    saida, i = [], 0
    argv = list(argv)
    while i < len(argv):
        a = argv[i]
        if a in ("--origem", "--destino"):
            saida.append(f"{a}={argv[i + 1]}")
            i += 2
        else:
            saida.append(a)
            i += 1
    return saida


class Fakes:
    def __init__(self):
        self.carregados = 0
        self.kwargs_carregar = []
        self.fabricas = 0
        self.consultas = []
        self.exibido = None

    def carregar(self, **kwargs):
        self.carregados += 1
        self.kwargs_carregar.append(kwargs)
        return _grafo()

    def factory(self):
        self.fabricas += 1

        def consultar(lat, lon):
            self.consultas.append((lat, lon))
            return {"currentSpeed": 10, "freeFlowSpeed": 120}

        return consultar

    def exibir(self, G, resumos):
        self.exibido = (G, resumos)

    def rodar(self, *argv):
        return cli.main(_norm(argv), carregar=self.carregar, consultar_factory=self.factory, exibir=self.exibir)


@pytest.fixture
def fk():
    return Fakes()


def test_sem_transito_todos_os_criterios(fk, capsys):
    assert fk.rodar("--origem", S, "--destino", T, "--sem-transito") == 0
    out = capsys.readouterr().out
    for rotulo in ("menor distância", "menor tempo", "menor consumo"):
        assert rotulo in out
    assert fk.fabricas == 0 and fk.consultas == []
    assert fk.carregados == 1
    assert fk.exibido is None


def test_criterio_tempo_so_uma_linha(fk, capsys):
    assert fk.rodar("--origem", S, "--destino", T, "--sem-transito", "--criterio", "tempo") == 0
    out = capsys.readouterr().out
    assert "menor tempo" in out
    assert "menor distância" not in out and "menor consumo" not in out


@pytest.mark.parametrize("nome", ["distancia", "consumo"])
def test_criterio_unico(fk, capsys, nome):
    assert fk.rodar("--origem", S, "--destino", T, "--sem-transito", "--criterio", nome) == 0
    out = capsys.readouterr().out
    assert sum(r in out for r in ("menor distância", "menor tempo", "menor consumo")) == 1


def test_criterio_todos_explicito(fk, capsys):
    assert fk.rodar("--origem", S, "--destino", T, "--sem-transito", "--criterio", "todos") == 0
    assert "menor tempo" in capsys.readouterr().out


def test_com_transito_usa_consultar_da_factory(fk, capsys):
    assert fk.rodar("--origem", S, "--destino", T) == 0
    assert fk.fabricas == 1
    assert fk.consultas  # as vias primary foram consultadas (falsa, sem rede)
    assert "menor tempo" in capsys.readouterr().out


def test_geojson_grava_featurecollection(fk, tmp_path, capsys):
    arq = tmp_path / "rotas.geojson"
    assert fk.rodar("--origem", S, "--destino", T, "--sem-transito", "--geojson", str(arq)) == 0
    dados = json.loads(arq.read_text(encoding="utf-8"))
    assert dados["type"] == "FeatureCollection"
    assert [f["properties"]["criterio"] for f in dados["features"]] == ["distancia", "tempo", "consumo"]
    for f in dados["features"]:
        assert f["geometry"]["type"] == "LineString"
        assert f["geometry"]["coordinates"][0] == [-38.5, -3.8]
        assert f["geometry"]["coordinates"][-1] == [-38.46, -3.8]
    assert str(arq) in capsys.readouterr().out


def test_geojson_com_criterio_unico_tem_uma_feature(fk, tmp_path):
    arq = tmp_path / "r.geojson"
    assert fk.rodar("--origem", S, "--destino", T, "--sem-transito", "--criterio", "consumo",
                    "--geojson", str(arq)) == 0
    assert len(json.loads(arq.read_text(encoding="utf-8"))["features"]) == 1


def test_mostrar_chama_exibir_com_grafo_e_resumos(fk):
    assert fk.rodar("--origem", S, "--destino", T, "--sem-transito", "--mostrar") == 0
    G, resumos = fk.exibido
    assert set(resumos) == set(Criterio)
    assert "s" in G


def test_origem_e_destino_por_nome_de_rua(fk, capsys):
    # "Avenida Rapida" resolve para o cruzamento "f" (seguinte ao 1o trecho); de la ate t existe rota
    assert fk.rodar("--origem", "avenida rapida", "--destino", T, "--sem-transito") == 0
    assert "menor tempo" in capsys.readouterr().out


def test_sem_tomtom_key_codigo_2_sem_traceback(monkeypatch, capsys):
    monkeypatch.delenv("TOMTOM_KEY", raising=False)
    chamado = []
    r = cli.main(["--origem=" + S, "--destino=" + T],
                 carregar=lambda: chamado.append(1) or _grafo(), exibir=lambda *a: chamado.append(2))
    assert r == 2
    cap = capsys.readouterr()
    assert "TOMTOM_KEY" in cap.err
    assert "--sem-transito" in cap.err
    assert "Traceback" not in cap.err and "Traceback" not in cap.out
    assert chamado == []  # nem carregou o grafo


def test_sem_tomtom_key_mas_com_sem_transito_funciona(monkeypatch, fk):
    monkeypatch.delenv("TOMTOM_KEY", raising=False)
    r = cli.main(["--origem=" + S, "--destino=" + T, "--sem-transito"],
                 carregar=fk.carregar, exibir=fk.exibir)
    assert r == 0


@pytest.mark.parametrize("origem,destino", [
    ("999,0", T),                # latitude fora do intervalo
    (S, "0,999"),                # longitude fora do intervalo
    ("Rua Inexistente", T),      # rua nao encontrada
    (S, "Rua Inexistente"),
])
def test_origem_ou_destino_invalido_codigo_2(fk, capsys, origem, destino):
    assert fk.rodar("--origem", origem, "--destino", destino, "--sem-transito") == 2
    cap = capsys.readouterr()
    assert cap.err.startswith("erro:")
    assert "Traceback" not in cap.err
    assert cap.out == ""


def test_destino_inalcancavel_codigo_2(fk, capsys):
    # t -> s nao existe (mao unica)
    assert fk.rodar("--origem", T, "--destino", S, "--sem-transito") == 2
    assert "erro:" in capsys.readouterr().err


def test_argumentos_obrigatorios_ausentes_saem_com_2(fk):
    with pytest.raises(SystemExit) as e:
        fk.rodar("--sem-transito")
    assert e.value.code == 2


def test_criterio_desconhecido_rejeitado_pelo_argparse(fk):
    with pytest.raises(SystemExit) as e:
        fk.rodar("--origem", S, "--destino", T, "--criterio", "beleza")
    assert e.value.code == 2


def test_consultar_padrao_sem_chave_levanta_runtimeerror(monkeypatch):
    monkeypatch.delenv("TOMTOM_KEY", raising=False)
    with pytest.raises(RuntimeError):
        cli.consultar_padrao()


def test_consultar_padrao_com_chave_devolve_consultar_com_cache(monkeypatch):
    monkeypatch.setenv("TOMTOM_KEY", "chave-falsa")
    monkeypatch.setattr(cli.transito, "com_cache", lambda *a, **k: "consultar-falso")
    assert cli.consultar_padrao() == "consultar-falso"


def test_main_module_importa_cli_main():
    import importlib.util

    spec = importlib.util.find_spec("tonton.__main__")
    assert spec is not None


def test_atualizar_grafo_chama_carregar_sem_cache(fk):
    assert fk.rodar("--origem", S, "--destino", T, "--sem-transito", "--atualizar-grafo") == 0
    assert fk.kwargs_carregar == [{"usar_cache": False}]


def test_sem_atualizar_grafo_chama_carregar_sem_argumentos(fk):
    assert fk.rodar("--origem", S, "--destino", T, "--sem-transito") == 0
    assert fk.kwargs_carregar == [{}]


def test_origem_com_espaco_e_lat_negativa_aceita(fk):
    assert cli.main(["--origem", S, "--destino", T, "--sem-transito"],
                    carregar=fk.carregar, exibir=fk.exibir) == 0
