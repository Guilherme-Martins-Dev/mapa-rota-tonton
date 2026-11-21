"""Etapa 1 (Kokoro). Rodar: cd /d/projetos/NeuroSim_3D/spikes/conversa/local && uv run python <este arquivo> [cena ...]"""
import json, sys, soundfile as sf
from pathlib import Path
from kokoro_onnx import Kokoro
AQUI = Path(__file__).resolve().parent
M = Path("D:/projetos/NeuroSim_3D/spikes/conversa/local/modelos/kokoro")
cfg = json.loads((AQUI / "roteiro.json").read_text(encoding="utf-8"))
k = Kokoro(str(M / "kokoro-v1.0.onnx"), str(M / "voices-v1.0.bin"))
for cena, frases in cfg["cenas"].items():
    if len(sys.argv) > 1 and cena not in sys.argv[1:]: continue
    for i, f in enumerate(frases):
        a, sr = k.create(f["t"], voice=cfg["voz_base"], speed=cfg["velocidade"], lang="pt-br")
        sf.write(AQUI / "audio" / "base" / f"{cena}_{i:02d}.wav", a, sr)
    print("base", cena, len(frases), "frases", flush=True)
