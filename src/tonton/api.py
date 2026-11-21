"""API HTTP da demonstração: endereço de origem e destino -> rotas por distância, tempo e consumo.

Rodar: uvicorn tonton.api:app --port 8000   (o front em dev faz proxy de /api).
Endereço aceito: "lat,lon" ou nome de rua do grafo (sem acento e sem caixa). Nada é enviado a serviços externos.
"""
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query

from tonton import consumo, planejador
from tonton.grafo import carregar_grafo
from tonton.planejador import Criterio
from tonton.rotas import RotaInexistente
from tonton.ruas import agrupar_por_rua, normalizar
from tonton.simulacao import aplicar_transito_simulado
from tonton.veiculos import carregar_catalogo, veiculo_do_catalogo

DISTANCIA_MAX_M = 1500.0  # ponto mais longe que isso do cruzamento mais próximo está fora da área do grafo


def criar_app(G=None) -> FastAPI:
    """`G` injeta um grafo já preparado (testes); sem ele, carrega o grafo de Messejana no startup."""
    estado: dict = {"G": G, "nomes": None}
    trava = threading.Lock()  # o consumo é regravado nas arestas a cada requisição

    @asynccontextmanager
    async def ciclo(_app):
        if estado["G"] is None:
            estado["G"] = aplicar_transito_simulado(carregar_grafo())
        estado["nomes"] = sorted(agrupar_por_rua(estado["G"]))
        yield

    app = FastAPI(title="Rotas de Messejana", lifespan=ciclo)

    @app.get("/api/veiculos")
    def veiculos():
        return [{k: v for k, v in item.items()} for item in carregar_catalogo()]

    @app.get("/api/ruas")
    def ruas(q: str = Query(min_length=2, max_length=60)):
        alvo = normalizar(q)
        return [n for n in estado["nomes"] or [] if alvo in normalizar(n)][:8]

    def _ponto(texto: str, rotulo: str):
        G = estado["G"]
        try:
            no = planejador.resolver_ponto(G, texto)
        except ValueError as e:
            raise HTTPException(422, f"{rotulo}: {e}") from e
        lat, lon = G.nodes[no]["y"], G.nodes[no]["x"]
        m = planejador._COORD.match(texto)
        if m and planejador._haversine_m(float(m.group(1)), float(m.group(2)), lat, lon) > DISTANCIA_MAX_M:
            raise HTTPException(422, f"{rotulo}: coordenada fora da área de Messejana")
        return no, lat, lon

    @app.get("/api/rotas")
    def rotas(origem: str = Query(min_length=2, max_length=80), destino: str = Query(min_length=2, max_length=80),
              veiculo: str = "popular"):
        try:
            v = veiculo_do_catalogo(veiculo)
        except KeyError:
            raise HTTPException(422, f"veículo desconhecido: {veiculo!r}") from None
        o, olat, olon = _ponto(origem, "origem")
        d, dlat, dlon = _ponto(destino, "destino")
        if o == d:
            raise HTTPException(422, "origem e destino resolvem para o mesmo cruzamento")
        G = estado["G"]
        with trava:
            consumo.atribuir_consumo(G, v)
            try:
                resumos = planejador.planejar(G, o, d, veiculo=v)
            except RotaInexistente as e:
                raise HTTPException(404, "não há caminho entre os pontos informados") from e
            colecao = planejador.geojson_colecao(G, [resumos[c] for c in Criterio])
        colecao["metadados"] = {
            "origem": {"entrada": origem, "lat": olat, "lon": olon},
            "destino": {"entrada": destino, "lat": dlat, "lon": dlon},
            "veiculo": veiculo,
            "transito": "simulado",
        }
        return colecao

    return app


app = criar_app()
