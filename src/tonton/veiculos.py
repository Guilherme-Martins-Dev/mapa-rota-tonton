"""Catálogo de veículos: calibra a curva de consumo a partir de consumo urbano e de estrada.

L/100km = a + b/v + c*v² (ver consumo.py). Com o consumo urbano (v_urbano) e o de estrada (v_estrada)
fixamos a = FRACAO_A * estrada e resolvemos b e c por um sistema linear 2x2. Os campos do catálogo
(`consumo_urbano_l100`, `consumo_estrada_l100`) seguem o esquema do Car3DB (fuel consumption city/highway),
para trocar o catálogo por dados completos licenciados sem mexer no código.
"""
import json
from pathlib import Path

from tonton.consumo import PADRAO, Veiculo

V_URBANO_KMH = 30.0  # velocidade em que o consumo "urbano" vale
V_ESTRADA_KMH = 90.0  # velocidade em que o consumo "de estrada" vale
FRACAO_A = 0.44  # a / estrada; no PADRAO (carro popular) a ≈ 0,44 do consumo a 90 km/h
CATALOGO = Path(__file__).with_name("veiculos.json")


def calibrar(nome: str, urbano_l100: float, estrada_l100: float) -> Veiculo:
    """Veiculo cuja curva passa por (30 km/h, urbano) e (90 km/h, estrada). Valores devem ser positivos."""
    if urbano_l100 <= 0 or estrada_l100 <= 0:
        raise ValueError(f"consumos devem ser positivos: urbano={urbano_l100}, estrada={estrada_l100}")
    a = FRACAO_A * estrada_l100
    r1, r2 = urbano_l100 - a, estrada_l100 - a
    u, e = V_URBANO_KMH, V_ESTRADA_KMH
    # b/u + c*u² = r1 ;  b/e + c*e² = r2   ->   Cramer
    det = (1 / u) * e**2 - (1 / e) * u**2
    b = (r1 * e**2 - r2 * u**2) / det
    c = ((1 / u) * r2 - (1 / e) * r1) / det
    if b <= 0 or c <= 0:  # perfil fora do formato em U (ex.: estrada muito pior que cidade): escala o PADRAO
        k = (urbano_l100 + estrada_l100) / (_padrao_em(u) + _padrao_em(e))
        return Veiculo(nome, PADRAO.a * k, PADRAO.b * k, PADRAO.c * k)
    return Veiculo(nome, a, b, c)


def _padrao_em(v: float) -> float:
    return PADRAO.a + PADRAO.b / v + PADRAO.c * v**2


def carregar_catalogo(caminho: Path = CATALOGO) -> list[dict]:
    """Lista de entradas do catálogo (dicts como no JSON)."""
    return json.loads(caminho.read_text(encoding="utf-8"))


def veiculo_do_catalogo(id_: str, catalogo: list[dict] | None = None) -> Veiculo:
    for item in catalogo if catalogo is not None else carregar_catalogo():
        if item["id"] == id_:
            return calibrar(item["nome"], item["consumo_urbano_l100"], item["consumo_estrada_l100"])
    raise KeyError(id_)
