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
