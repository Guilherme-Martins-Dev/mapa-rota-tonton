"""Etapa 4: consumo de combustível em função da velocidade (curva em U).

L/100km = a + b/v + c*v², com v em km/h. O termo b/v pesa em trânsito lento, c*v² em
velocidade alta; o mínimo fica em v = (b / 2c)^(1/3).
"""
import math
from dataclasses import dataclass

from tonton.pesos import velocidade_livre_osm
from tonton.rotas import Rota, menor_rota


@dataclass(frozen=True)
class Veiculo:
    nome: str
    a: float  # L/100km, parcela constante
    b: float  # L/100km * km/h, domina em baixa velocidade
    c: float  # L/100km / (km/h)², domina em alta velocidade
    v_piso_kmh: float = 5.0  # velocidade mínima usada na curva (evita divisão por zero)


# Carro popular: mínimo de ~6,5 L/100km perto de 65 km/h.
PADRAO = Veiculo("popular", a=3.04, b=150.0, c=2.73e-4)


def velocidade_otima_kmh(veiculo: Veiculo = PADRAO) -> float:
    """Velocidade (km/h) de menor consumo: (b / 2c)^(1/3)."""
    return (veiculo.b / (2 * veiculo.c)) ** (1 / 3)


def consumo_l_por_100km(v_kmh: float | None, veiculo: Veiculo = PADRAO) -> float:
    """Consumo em L/100km a v_kmh. v None, nan ou abaixo do piso usa o piso do veículo."""
    if v_kmh is None or math.isnan(v_kmh) or v_kmh < veiculo.v_piso_kmh:
        v_kmh = veiculo.v_piso_kmh
    return veiculo.a + veiculo.b / v_kmh + veiculo.c * v_kmh ** 2


def litros(comprimento_m: float | None, v_kmh: float | None, veiculo: Veiculo = PADRAO) -> float:
    """Litros gastos num trecho: km * L/100km / 100. Sem comprimento: inf."""
    if comprimento_m is None:
        return math.inf
    return (comprimento_m / 1000) * consumo_l_por_100km(v_kmh, veiculo) / 100


def atribuir_consumo(G, veiculo: Veiculo = PADRAO):
    """Grava `litros` em cada aresta, a partir de v_atual (sem ele: velocidade livre do OSM)."""
    for _, _, dados in G.edges(data=True):
        v = dados.get("v_atual")
        if v is None:
            v = velocidade_livre_osm(dados)
        dados["litros"] = litros(dados.get("length"), v, veiculo)
    return G


def rota_menor_consumo(G, origem, destino) -> Rota:
    """Rota de menor consumo (custo em litros). Exige atribuir_consumo antes."""
    return menor_rota(G, origem, destino, peso="litros")
