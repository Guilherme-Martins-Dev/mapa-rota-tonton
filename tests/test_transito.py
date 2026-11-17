import pytest

from tonton import transito


class RespostaFalsa:
    def raise_for_status(self):
        pass

    def json(self):
        return {"flowSegmentData": {"currentSpeed": 20, "freeFlowSpeed": 40}}


def test_consultar_trafego_monta_requisicao_e_devolve_fluxo(monkeypatch):
    monkeypatch.setenv("TOMTOM_KEY", "k")
    chamada = {}

    def get_falso(url, params, timeout):
        chamada.update(url=url, params=params)
        return RespostaFalsa()

    monkeypatch.setattr(transito.requests, "get", get_falso)
    fluxo = transito.consultar_trafego(-3.8267, -38.4935)

    assert fluxo == {"currentSpeed": 20, "freeFlowSpeed": 40}
    assert chamada["params"]["point"] == "-3.8267,-38.4935"
    assert chamada["params"]["key"] == "k"


def relogio(inicio=1000.0):
    t = [inicio]
    return (lambda: t[0]), t


def test_cache_evita_segunda_consulta_dentro_da_validade(tmp_path):
    chamadas = []
    agora, t = relogio()
    c = transito.com_cache(lambda la, lo: chamadas.append((la, lo)) or {"currentSpeed": 20},
                           tmp_path / "t.json", validade_s=60, agora=agora)
    assert c(-3.8, -38.5) == {"currentSpeed": 20}
    t[0] += 59
    assert c(-3.8, -38.5) == {"currentSpeed": 20}
    assert len(chamadas) == 1


def test_cache_expira_e_consulta_de_novo(tmp_path):
    chamadas = []
    agora, t = relogio()
    c = transito.com_cache(lambda la, lo: chamadas.append(1) or {"n": len(chamadas)},
                           tmp_path / "t.json", validade_s=60, agora=agora)
    c(-3.8, -38.5)
    t[0] += 61
    assert c(-3.8, -38.5) == {"n": 2}


def test_cache_persiste_entre_execucoes(tmp_path):
    agora, _ = relogio()
    arq = tmp_path / "t.json"
    transito.com_cache(lambda la, lo: {"v": 1}, arq, 60, agora)(-3.8, -38.5)

    def nao_deveria_chamar(la, lo):
        raise AssertionError("consultou a TomTom de novo")

    assert transito.com_cache(nao_deveria_chamar, arq, 60, agora)(-3.8, -38.5) == {"v": 1}


def test_cache_nao_guarda_falha(tmp_path):
    agora, _ = relogio()
    arq = tmp_path / "t.json"

    def falha(la, lo):
        raise RuntimeError("cota esgotada")

    c = transito.com_cache(falha, arq, 60, agora)
    with pytest.raises(RuntimeError):
        c(-3.8, -38.5)
    assert not arq.exists()


def test_cache_ignora_arquivo_corrompido(tmp_path):
    agora, _ = relogio()
    arq = tmp_path / "t.json"
    arq.write_text("{isso não é json", encoding="utf-8")
    assert transito.com_cache(lambda la, lo: {"v": 2}, arq, 60, agora)(-3.8, -38.5) == {"v": 2}
