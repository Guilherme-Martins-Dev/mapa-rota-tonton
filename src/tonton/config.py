import os
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parents[2]
CACHE = RAIZ / "cache"

LUGAR = "Messejana, Fortaleza, Ceará, Brazil"

load_dotenv(RAIZ / ".env")


def tomtom_key() -> str:
    """Chave da TomTom, lida de TOMTOM_KEY (variável de ambiente ou .env)."""
    chave = os.environ.get("TOMTOM_KEY", "").strip()
    if not chave:
        raise RuntimeError("TOMTOM_KEY não definida: copie .env.example para .env e preencha.")
    return chave
