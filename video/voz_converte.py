"""Etapa 2 (OpenVoice, timbre da referência). Rodar DENTRO de NeuroSim/.../voz-openvoice: .venv/Scripts/python.exe <este arquivo> [cena ...]"""
import json, sys, numpy as np, soundfile as sf
from pathlib import Path
sys.path.insert(0, "OpenVoice")
from openvoice.api import ToneColorConverter
VIDEO = Path("D:/Estudo/grafos/mapa-rota-tonton/video"); cfg = json.loads((VIDEO / "roteiro.json").read_text(encoding="utf-8"))
c = ToneColorConverter("checkpoints_v2/converter/config.json", device="cpu")
c.load_ckpt("checkpoints_v2/converter/checkpoint.pth")
tgt = c.extract_se(["referencia.wav"])
for cena, frases in cfg["cenas"].items():
    if len(sys.argv) > 1 and cena not in sys.argv[1:]: continue
    partes, sr, tempos, t = [], None, [], 0.0
    for i, f in enumerate(frases):
        base = VIDEO / "audio" / "base" / f"{cena}_{i:02d}.wav"; saida = VIDEO / "audio" / "conv" / f"{cena}_{i:02d}.wav"
        c.convert(audio_src_path=str(base), src_se=c.extract_se([str(base)]), tgt_se=tgt, output_path=str(saida), message="default", tau=cfg["tau"])
        a, sr = sf.read(saida); dur = len(a) / sr
        tempos.append({"ini": round(t, 2), "fim": round(t + dur, 2), "l": f["l"]}); t += dur + f.get("pausa", 0.3)
        partes += [a, np.zeros(int(sr * f.get("pausa", 0.3)))]
    sf.write(VIDEO / "audio" / "cenas" / f"{cena}.wav", np.concatenate(partes[:-1]), sr)
    (VIDEO / "audio" / "cenas" / f"{cena}.json").write_text(json.dumps({"duracao": round(t - f.get("pausa", 0.3), 2), "frases": tempos}, ensure_ascii=False), encoding="utf-8")
    print("cena", cena, f"{t:.1f}s", flush=True)
