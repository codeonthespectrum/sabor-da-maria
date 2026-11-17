#!/usr/bin/env python3
"""Gera docs/demo/demo.mp4: a sessão real do WhatsApp renderizada como
vídeo de chat (frames via Chrome headless, montagem via ffmpeg).

Mensagens longas são percorridas com scroll progressivo — o vídeo nunca
"pula" para o fim de uma bolha sem mostrar o começo.

Uso: .venv/bin/python scripts/gerar_demo_video.py
Fonte: backups/20261115_181242_4c73195e-sauda-o-amig-vel.md (transcrição real)
"""

import html
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EXPORT = REPO / "backups" / "20261115_181242_4c73195e-sauda-o-amig-vel.md"
SAIDA = REPO / "docs" / "demo" / "demo.mp4"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
FFMPEG = "ffmpeg"

W, H = 720, 1280          # janela lógica; screenshots saem em 2x (retina)
CHAT_TOP = 110            # altura do header
VIEWPORT = H - CHAT_TOP   # área útil do chat
PASSO_SCROLL = 750        # px por passo de rolagem em mensagens longas
ALTURA_TYPING = 60        # bolha de "digitando" (aprox.)


# ------------------------------------------------------------------ parsing

def carregar_mensagens():
    md = EXPORT.read_text(encoding="utf-8").split("## Export verification")[0]
    msgs = []
    for b in re.split(r"\n### ", md)[1:]:
        papel = b.split(" — ")[0].strip()
        if papel not in ("User", "Assistant"):
            continue
        corpo = b.split("\n", 1)[1].split("## Tool calls")[0].strip()
        if corpo:
            msgs.append(("out" if papel == "User" else "in", corpo))
    return msgs


def fmt_bolha(texto: str) -> str:
    """Markdown do WhatsApp -> HTML da bolha; linhas de tabela em mono."""
    linhas = []
    for ln in texto.split("\n"):
        ln = html.escape(ln)
        ln = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", ln)  # ** antes de *
        ln = re.sub(r"\*([^*]+)\*", r"<b>\1</b>", ln)
        ln = re.sub(r"_([^_]+)_", r"<i>\1</i>", ln)
        if ln.lstrip().startswith("|"):
            ln = f'<span class="mono">{ln}</span>'
        linhas.append(ln)
    corpo = "<br>".join(linhas)
    if "cardapio_lancamento.pdf" in corpo and "MEDIA:" in corpo:
        corpo = ('<div class="doc">📄 <b>cardapio_lancamento.pdf</b>'
                 '<br><span class="docsub">PDF • Cardápio de lançamento</span></div>')
    return corpo


# ------------------------------------------------------------------ HTML

CSS = """
* { box-sizing: border-box; }
body { margin:0; font-family:-apple-system,'SF Pro Text','Segoe UI',Roboto,sans-serif;
       background:#ECE5DD; height:1280px; overflow:hidden; }
.header { background:#075E54; color:#fff; padding:26px 22px 20px; display:flex;
          align-items:center; gap:16px; height:110px; }
.avatar { width:64px; height:64px; border-radius:50%; background:#DFE5E7; display:flex;
          align-items:center; justify-content:center; font-size:36px; }
.hname { font-size:30px; font-weight:600; }
.hstatus { font-size:22px; color:#C8E6C9; margin-top:2px; }
.chatwrap { height:1170px; overflow:hidden; position:relative; }
.chat { padding:24px 18px; display:flex; flex-direction:column; gap:12px;
        position:relative; }
.msg { max-width:78%; padding:12px 14px 8px; border-radius:12px; font-size:26px;
       line-height:1.38; box-shadow:0 1px 1px rgba(0,0,0,.18); overflow-wrap:anywhere; }
.in  { align-self:flex-start; background:#fff; border-top-left-radius:3px; }
.out { align-self:flex-end; background:#DCF8C6; border-top-right-radius:3px; }
.time { font-size:18px; color:#9aa5a9; float:right; margin:10px 0 0 14px; }
.mono { font-family:'SF Mono',Menlo,monospace; font-size:20px; white-space:pre; }
.doc  { background:#075E5410; border:1px solid #075E5430; border-radius:8px;
        padding:10px 12px; font-size:24px; }
.docsub { font-size:20px; color:#667; }
.typing { display:flex; gap:8px; padding:16px 18px; }
.dot { width:12px; height:12px; border-radius:50%; background:#b3b8ba; }
.card { width:720px; height:1280px; background:#075E54; color:#fff; display:flex;
        flex-direction:column; align-items:center; justify-content:center; gap:18px;
        text-align:center; padding:60px; }
.card h1 { font-size:44px; margin:0; }
.card p  { font-size:26px; color:#C8E6C9; margin:0; line-height:1.5; }
.card .small { font-size:22px; color:#9ec7b3; }
"""


def header(status: str) -> str:
    return (f'<div class="header"><div class="avatar">🍳</div><div>'
            f'<div class="hname">Consultora Sabor da Maria</div>'
            f'<div class="hstatus">{status}</div></div></div>')


def bolha(quem: str, texto: str, hora: str) -> str:
    return (f'<div class="msg {quem}">{fmt_bolha(texto)}'
            f'<span class="time">{hora}</span></div>')


TYPING = ('<div class="msg in typing"><div class="dot"></div>'
          '<div class="dot"></div><div class="dot"></div></div>')


def pagina_chat(status: str, bolhas: list[str], offset: int,
                typing: bool = False) -> str:
    conteudo = "".join(bolhas) + (TYPING if typing else "")
    return ("<!doctype html><meta charset='utf-8'>"
            f"<style>{CSS}</style><body>{header(status)}"
            f'<div class="chatwrap"><div class="chat" '
            f'style="transform: translateY(-{offset}px)">'
            f"{conteudo}</div></div></body>")


def pagina_card(inner: str) -> str:
    return (f"<!doctype html><meta charset='utf-8'><style>{CSS}</style>"
            f'<body class="card">{inner}</body>')


# ------------------------------------------------- medição real das bolhas

def medir_bolhas(bolhas: list[str], tmp: Path) -> list[dict]:
    """Uma passada de Chrome: offsetTop/offsetHeight de cada bolha."""
    js = ("window.onload=()=>{const e=[...document.querySelectorAll('.msg')];"
          "document.title=JSON.stringify(e.map(x=>({t:x.offsetTop,"
          "h:x.offsetHeight})));};")
    pag = ("<!doctype html><meta charset='utf-8'>"
           f"<style>{CSS}</style><body>"
           f'<div class="chatwrap" style="height:auto;overflow:visible">'
           f'<div class="chat">{"".join(bolhas)}</div></div>'
           f"<script>{js}</script></body>")
    med = tmp / "medir.html"
    med.write_text(pag, encoding="utf-8")
    out = subprocess.run(
        [CHROME, "--headless=new", "--disable-gpu", f"--window-size={W},{H}",
         "--virtual-time-budget=2000", "--dump-dom", f"file://{med}"],
        check=True, capture_output=True, text=True).stdout
    titulo = re.search(r"<title>(.*?)</title>", out, re.S).group(1)
    return json.loads(html.unescape(titulo))


# ------------------------------------------------------------------ frames

def main():
    msgs = carregar_mensagens()
    print(f"{len(msgs)} mensagens na transcrição")
    tmp = Path(tempfile.mkdtemp(prefix="demo_video_"))

    hora_min = 18 * 60 + 12
    bolhas, horas = [], []

    def hora():
        nonlocal hora_min
        h = f"{hora_min // 60:02d}:{hora_min % 60:02d}"
        hora_min += 2
        return h

    for quem, texto in msgs:
        horas.append(hora())
        bolhas.append(bolha(quem, texto, horas[-1]))

    dims = medir_bolhas(bolhas, tmp)
    assert len(dims) == len(msgs)

    frames = []  # (html, duracao_s)
    frames.append((pagina_card(
        "<h1>🍳 Sabor da Maria</h1>"
        "<p>Da despensa ao cardápio de lançamento,<br>pelo WhatsApp.</p>"
        "<p class='small'>Sessão real • agente Hermes + núcleo determinístico</p>"),
        3.0))

    offset = 0  # scroll atual (px)
    visiveis: list[str] = []

    for i, (quem, texto) in enumerate(msgs):
        # alvo: fim da bolha i visível com folga inferior de 24px
        alvo = max(0, dims[i]["t"] + dims[i]["h"] + 24 - VIEWPORT + 24)

        if quem == "in":
            # "digitando..." ancorado no fim do que já existe
            alvo_typing = max(0, dims[i]["t"] - 12 + ALTURA_TYPING + 24 - VIEWPORT + 24)
            frames.append((pagina_chat("digitando...", visiveis,
                                       max(offset, alvo_typing), typing=True), 0.9))
            offset = max(offset, alvo_typing)

        visiveis.append(bolhas[i])

        # scroll progressivo até o alvo (mensagem longa entra por partes)
        while alvo - offset > PASSO_SCROLL:
            offset += PASSO_SCROLL
            frames.append((pagina_chat("online", visiveis, offset), 0.75))
        offset = alvo

        leitura = max(1.6, min(9.0, len(texto) / 45)) if quem == "in" \
            else max(1.3, len(texto) / 70)
        frames.append((pagina_chat("online", visiveis, offset), leitura))

    frames.append((pagina_card(
        "<h1>✅ Cardápio entregue em PDF</h1>"
        "<p>3 pratos precificados • lista de compras R$ 23,00<br>"
        "sobra do orçamento R$ 57,00</p>"
        "<p class='small'>github.com/codeonthespectrum/sabor-da-maria</p>"),
        4.0))

    concat = tmp / "concat.txt"
    linhas = []
    for i, (pag, dur) in enumerate(frames):
        html_path = tmp / f"frame_{i:03d}.html"
        png_path = tmp / f"frame_{i:03d}.png"
        html_path.write_text(pag, encoding="utf-8")
        subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
             f"--window-size={W},{H}", "--force-device-scale-factor=2",
             f"--screenshot={png_path}", f"file://{html_path}"],
            check=True, capture_output=True)
        linhas += [f"file '{png_path}'", f"duration {dur:.2f}"]
    linhas.append(f"file '{png_path}'")  # concat exige repetir o último
    concat.write_text("\n".join(linhas), encoding="utf-8")

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
         "-vf", f"scale={W}:{H}", "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-crf", "26", "-movflags", "+faststart", str(SAIDA)],
        check=True, capture_output=True)
    mb = SAIDA.stat().st_size / 1e6
    print(f"vídeo gerado: {SAIDA} ({mb:.1f} MB, {len(frames)} frames)")


if __name__ == "__main__":
    sys.exit(main())
