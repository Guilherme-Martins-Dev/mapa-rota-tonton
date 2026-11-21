import pytest

from tonton.consumo import PADRAO, consumo_l_por_100km
from tonton.veiculos import V_ESTRADA_KMH, V_URBANO_KMH, calibrar, carregar_catalogo, veiculo_do_catalogo


def test_calibrar_passa_pelos_dois_pontos():
    v = calibrar("x", 10.5, 7.6)
    assert consumo_l_por_100km(V_URBANO_KMH, v) == pytest.approx(10.5, abs=1e-6)
    assert consumo_l_por_100km(V_ESTRADA_KMH, v) == pytest.approx(7.6, abs=1e-6)


def test_calibrar_mantem_formato_em_u():
    v = calibrar("x", 12.8, 9.2)
    assert v.b > 0 and v.c > 0
    assert consumo_l_por_100km(5, v) > consumo_l_por_100km(60, v) < consumo_l_por_100km(140, v)


def test_calibrar_perfil_fora_do_u_escala_o_padrao():
    v = calibrar("x", 4.0, 9.0)  # b negativo: sem solução em U
    assert v.b > 0 and v.c > 0
    assert v.b / v.a == pytest.approx(PADRAO.b / PADRAO.a)


@pytest.mark.parametrize("urbano,estrada", [(0, 5), (5, 0), (-1, 5)])
def test_calibrar_rejeita_consumo_nao_positivo(urbano, estrada):
    with pytest.raises(ValueError):
        calibrar("x", urbano, estrada)


def test_catalogo_completo_e_calibravel():
    itens = carregar_catalogo()
    assert {"popular", "golf-tdi"} <= {i["id"] for i in itens}
    for i in itens:
        v = veiculo_do_catalogo(i["id"], itens)
        assert consumo_l_por_100km(60, v) > 0
        assert i["origem"]


def test_veiculo_desconhecido():
    with pytest.raises(KeyError):
        veiculo_do_catalogo("nao-existe")
