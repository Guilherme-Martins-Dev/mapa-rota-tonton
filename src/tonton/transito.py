import requests

from tonton.config import tomtom_key

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
