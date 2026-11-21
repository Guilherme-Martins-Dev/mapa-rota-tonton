"""Trânsito SIMULADO para demonstração (a TomTom não é consultada).

v_atual = v_livre x fator em [0,5; 1,0] nas arestas TomTom, com semente fixa. Sem isso os três critérios
tendem a coincidir na mesma rota e a demonstração não teria o que comparar.
"""
import random

from tonton.pesos import atribuir_pesos, gravar_velocidades
from tonton.ruas import eh_tomtom

SEMENTE = 7


def aplicar_transito_simulado(G, semente: int = SEMENTE):
    """Grava pesos de tempo (sem TomTom) e depois v_atual simulada nas arestas de via principal."""
    atribuir_pesos(G)
    rng = random.Random(semente)
    for _, _, dados in G.edges(data=True):
        if eh_tomtom(dados):
            v = dados["v_livre"]
            gravar_velocidades(dados, v, v * rng.uniform(0.5, 1.0))
    return G
