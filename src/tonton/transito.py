import json
import time
from pathlib import Path

import requests

from tonton.config import CACHE, tomtom_key

URL_FLUXO = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"


def consultar_trafego(lat: float, lon: float) -> dict:
    """Fluxo do trecho mais próximo do ponto: currentSpeed (v_atual) e freeFlowSpeed (v_livre), em km/h."""
    r = requests.get(
        URL_FLUXO,
        params={"point": f"{lat},{lon}", "unit": "KMPH", "key": tomtom_key()},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()["flowSegmentData"]


ARQUIVO_CACHE = CACHE / "trafego.json"
VALIDADE_S = 15 * 60  # trânsito muda rápido: 15 min


def com_cache(consultar=consultar_trafego, arquivo=ARQUIVO_CACHE, validade_s=VALIDADE_S, agora=time.time):
    """Envolve `consultar(lat, lon)` com cache em disco (JSON) que expira em `validade_s` segundos.

    Poupa a cota da TomTom entre execuções. Só respostas bem-sucedidas são guardadas: se a consulta
    levantar erro, nada é gravado e o erro segue para o chamador (que decide o fallback).
    """
    arquivo = Path(arquivo)
    try:
        guardado = json.loads(arquivo.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        guardado = {}

    def consultar_com_cache(lat: float, lon: float) -> dict:
        chave = f"{lat:.5f},{lon:.5f}"
        item = guardado.get(chave)
        if item and agora() - item["quando"] < validade_s:
            return item["fluxo"]
        fluxo = consultar(lat, lon)
        guardado[chave] = {"quando": agora(), "fluxo": fluxo}
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        tmp = arquivo.with_suffix(".tmp")
        tmp.write_text(json.dumps(guardado), encoding="utf-8")
        tmp.replace(arquivo)  # troca atômica: um arquivo meio escrito nunca é lido
        return fluxo

    return consultar_com_cache
