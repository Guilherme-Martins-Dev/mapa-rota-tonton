import os, requests, getpass

# Lê a chave da variável de ambiente TOMTOM_KEY; se não existir, pede no terminal (sem mostrar)
TOMTOM_KEY = os.environ.get("TOMTOM_KEY") or getpass.getpass("Chave TomTom: ")

def consultar_trafego(lat, lon):
    # Traffic Flow - Flow Segment Data: velocidade atual x velocidade livre no trecho mais próximo do ponto
    url = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
    r = requests.get(url, params={"point": f"{lat},{lon}", "unit": "KMPH", "key": TOMTOM_KEY}, timeout=10)

    r.raise_for_status()
    return r.json()["flowSegmentData"]

# Ponto em Messejana, Fortaleza
dados = consultar_trafego(-3.826662, -38.493517)
print(f"Velocidade atual: {dados['currentSpeed']} km/h")
print(f"Velocidade livre: {dados['freeFlowSpeed']} km/h")
print(f"Tempo atual / livre: {dados['currentTravelTime']}s / {dados['freeFlowTravelTime']}s")

NOME_RUA = "Frei Cirilo"

def tem_nome(n):
    nomes = n if isinstance(n, str) else n["name"]
    return any(isinstance(x, str) and NOME_RUA.lower() in x.lower() for x in nomes)