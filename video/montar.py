"""Monta saida/rotas-de-messejana.mp4: para cada cena corta a captura, ajusta ao tempo da narração, queima legenda e junta.
Uso: python montar.py   (rodar dentro de video/)"""
import json, subprocess, sys
from pathlib import Path
AQUI = Path(__file__).resolve().parent
ORDEM = ["c1_gancho", "c2_apresenta", "c3_grafo", "c4_pesos", "c5_consumo", "c6_mapa", "c7_construcao", "c8_fecho"]
CAUDA = 0.5  # respiro após a última fala da cena

def sh(*a):
    r = subprocess.run([str(x) for x in a], cwd=AQUI, capture_output=True, text=True)
    if r.returncode: print(r.stderr[-1500:]); sys.exit(1)
    return r.stdout

def dur(arq):
    return float(sh("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", arq).strip())

def ts(s):
    h, m = int(s // 3600), int(s % 3600 // 60); return f"{h}:{m:02d}:{s % 60:05.2f}"

(AQUI / "scratch").mkdir(exist_ok=True)
partes = []
for cena in ORDEM:
    narr = json.loads((AQUI / "audio/cenas" / f"{cena}.json").read_text(encoding="utf-8"))
    cap = json.loads((AQUI / "captura" / f"{cena}.json").read_text(encoding="utf-8"))
    webm = f"captura/{cena}.webm"
    total = dur(webm)
    f = total / (cap["fim"] / 1000)           # relógio do vídeo / relógio real
    ini, seg = cap["inicio"] / 1000 * f, cap["ms"] / 1000 * f
    seg = min(seg, total - ini)
    alvo = narr["duracao"] + CAUDA
    print(f"{cena}: video {total:.1f}s f={f:.2f} ini={ini:.1f} seg={seg:.1f} -> alvo {alvo:.1f}s")
    # legenda ASS
    linhas = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080", "WrapStyle: 0", "",
              "[V4+ Styles]", "Format: Name,Fontname,Fontsize,PrimaryColour,OutlineColour,BackColour,Bold,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV",
              "Style: L,Segoe UI Semibold,46,&H00F3EDE8,&H00000000,&HB0140E0A,0,3,10,0,2,260,260,70", "",
              "[Events]", "Format: Layer,Start,End,Style,Text"]
    for fr in narr["frases"]:
        linhas.append(f"Dialogue: 0,{ts(fr['ini'])},{ts(fr['fim'] + 0.25)},L,{fr['l']}")
    (AQUI / "scratch" / f"{cena}.ass").write_text("\n".join(linhas), encoding="utf-8")
    out = f"scratch/{cena}.mp4"
    vf = (f"setpts=(PTS-STARTPTS)*{alvo / seg:.5f},fps=30,scale=1920:1080,fade=t=in:st=0:d=0.35,"
          f"ass=scratch/{cena}.ass")
    sh("ffmpeg", "-y", "-ss", f"{ini:.3f}", "-t", f"{seg:.3f}", "-i", webm, "-i", f"audio/cenas/{cena}.wav",
       "-filter_complex", f"[0:v]{vf}[v];[1:a]apad,atrim=0:{alvo:.3f},afade=t=in:d=0.05,afade=t=out:st={alvo - 0.3:.3f}:d=0.3[a]",
       "-map", "[v]", "-map", "[a]", "-t", f"{alvo:.3f}", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "192k", "-ar", "48000", out)
    partes.append(out)
(AQUI / "scratch" / "lista.txt").write_text("\n".join(f"file '{Path(p).name}'" for p in partes), encoding="utf-8")
sh("ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "scratch/lista.txt", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "saida/rotas-de-messejana.mp4")
print("OK", dur("saida/rotas-de-messejana.mp4"), "s")
