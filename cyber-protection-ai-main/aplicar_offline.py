"""
aplicar_offline.py — Hace que el frontend NO dependa de Internet (D-08).

Uso (desde cyber-protection-ai-main, con frontend/assets/vendor/ ya copiada):
    python aplicar_offline.py

Reemplaza los enlaces a CDN (Google Fonts, Tabler Icons, Chart.js) por copias
locales en frontend/assets/vendor/. Idempotente. Los respaldos de los archivos
se guardan FUERA del proyecto, en ../_respaldo_parches/offline/.
Al final lista cualquier referencia externa que haya quedado.
"""
import re, shutil, sys
from pathlib import Path

RAIZ = Path.cwd()
FRONT = RAIZ / "frontend"
RESP = RAIZ.parent / "_respaldo_parches" / "offline"

if not (FRONT / "assets/vendor/fonts/fonts.css").exists():
    sys.exit("❌ Falta frontend/assets/vendor/ (copie la carpeta del zip primero).")

def respaldar(p: Path):
    destino = RESP / p.relative_to(RAIZ)
    if not destino.exists():
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, destino)

def reescribir_html(p: Path, prefijo: str) -> bool:
    txt = orig = p.read_text(encoding="utf-8")
    # 1) preconnect a Google
    txt = re.sub(r'[ \t]*<link[^>]*rel="preconnect"[^>]*fonts\.(googleapis|gstatic)\.com[^>]*>\s*?\n', '', txt)
    # 2) hoja de estilos de Google Fonts -> fuentes locales
    txt = re.sub(r'<link[^>]*fonts\.googleapis\.com/css2[^>]*>',
                 f'<link rel="stylesheet" href="{prefijo}assets/vendor/fonts/fonts.css">', txt)
    # 3) Tabler Icons
    txt = re.sub(r'<link[^>]*cdn\.jsdelivr\.net/npm/@tabler/icons-webfont[^>]*>',
                 f'<link rel="stylesheet" href="{prefijo}assets/vendor/tabler/tabler-icons.min.css">', txt)
    # 4) Chart.js
    txt = re.sub(r'<script[^>]*cdnjs\.cloudflare\.com/ajax/libs/Chart\.js/[^>]*></script>',
                 f'<script src="{prefijo}assets/vendor/chartjs/chart.umd.min.js"></script>', txt)
    if txt != orig:
        respaldar(p); p.write_text(txt, encoding="utf-8")
        return True
    return False

cambiados = []
for p in sorted((FRONT / "pages").glob("*.html")):
    if reescribir_html(p, "../"): cambiados.append(p.relative_to(RAIZ))
idx = FRONT / "index.html"
if idx.exists() and reescribir_html(idx, ""): cambiados.append(idx.relative_to(RAIZ))

# base.css: @import de Google Fonts -> fuentes locales
base = FRONT / "css/base.css"
if base.exists():
    t = o = base.read_text(encoding="utf-8")
    t = re.sub(r"@import url\('https://fonts\.googleapis\.com[^']*'\);",
               "@import url('../assets/vendor/fonts/fonts.css');", t)
    if t != o:
        respaldar(base); base.write_text(t, encoding="utf-8"); cambiados.append(base.relative_to(RAIZ))

for c in cambiados: print("  ✔", c)
print(f"\nArchivos modificados: {len(cambiados)}")

# Revisión final: ¿queda algo externo?
patron = re.compile(r'(?:src|href)\s*=\s*"(https?://[^"]+)"|@import\s+url\([\'"]?(https?://[^\'")]+)|url\([\'"]?(https?://[^\'")]+)')
restos = []
for p in list(FRONT.rglob("*.html")) + list(FRONT.rglob("*.css")) + list(FRONT.rglob("*.js")):
    if "assets/vendor" in p.as_posix(): continue
    for m in patron.finditer(p.read_text(encoding="utf-8", errors="ignore")):
        url = next(g for g in m.groups() if g)
        if "w3.org" in url: continue
        restos.append((p.relative_to(RAIZ), url))
if restos:
    print("\n⚠ Quedan referencias externas (revisar):")
    for f, u in restos: print("  -", f, "→", u)
else:
    print("✅ Ninguna referencia externa en el frontend.")
