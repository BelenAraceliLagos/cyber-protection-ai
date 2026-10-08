"""
generate_proposal.py — Generador PDF con WeasyPrint.
Coordenadas pixel-perfect extraídas de propuesta_real.pdf con pdfplumber.

MEDIDAS EXACTAS (595.5 x 842.25 pts = A4):
─────────────────────────────────────────────────────────────────────
PORTADA (pág 1):
  Título:       x=59.5, y_top=118.3, font=38.5pt, bold, color=#155FCF
  "Preparado":  x=59.5, y=336.5,  font=17pt, bold
  Cliente:      x=59.5, y=387.5,  font=17pt, bold
  Objetivo:     x=59.5, y=464.0,  font=17pt, bold
  "Elaborado":  x=349.5, y=691.3, font=12pt, bold
  Zona texto:   x=59.5 → ~480, y=118 → ~650

INTERIORES estándar (págs 2,4,5,6,8):
  H1:           x=123.6, y_top≈261, font=26pt, bold, color=#155FCF
  Body:         x=125.5, y_start≈351, font=10.5pt, regular, justify
  Zona texto:   x=123.6 → 535.7, y=261 → ~720
  Firma:        centrada, y≈677-710

INTERIORES con banner (págs 3,7):
  Banner-título: zona verde centrada en x≈297-396, y≈150-176
  Body:          x=107.9 → 578.5, y_start≈337

MAPA mm para CSS (1pt = 0.353mm, página = 210x297mm):
  Portada content: left=21mm, top=41.8mm, width=150mm
  Interior content estándar: left=43.6mm, top=92.2mm, width=145mm
  Interior content con banner: left=38mm, top=52mm, width=155mm (banner arriba)
─────────────────────────────────────────────────────────────────────
"""

import os
import json
import base64
import os
import json
import base64
import requests as _requests
from pathlib import Path
from pathlib import Path

# ── Rutas assets ───────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent
ASSETS_DIR = (BASE_DIR / ".." / ".." / "assets").resolve()

BASE_PORTADA  = ASSETS_DIR / "base_portada.png"
BASE_INTERIOR = ASSETS_DIR / "base_interior.png"

# ── Colores corporativos ───────────────────────────────────────────────────
AZUL  = "#155FCF"
VERDE = "#8EE3C8"
GRIS  = "#4a4a4a"

# ── Mapeo de clave de fuente -> pila CSS real ───────────────────────────────
# IMPORTANTE: debe coincidir exactamente con FONT_STACKS en editor.html,
# para que la vista previa del editor y el PDF final se vean igual.
FONT_STACKS = {
    "segoe":     "'Segoe UI', 'Segoe UI Variable', Arial, sans-serif",
    "arial":     "Arial, Helvetica, sans-serif",
    "calibri":   "Calibri, 'Segoe UI', sans-serif",
    "georgia":   "Georgia, 'Times New Roman', serif",
    "times":     "'Times New Roman', Times, serif",
    "verdana":   "Verdana, Geneva, sans-serif",
    "trebuchet": "'Trebuchet MS', sans-serif",
}


def _font_stack(clave: str, custom_fonts: dict | None = None) -> str:
    """
    Resuelve la pila CSS font-family para una clave de fuente.
    Si la clave corresponde a una fuente personalizada (subida por el
    usuario), usa su nombre real declarado en @font-face; si no, cae a
    las fuentes del sistema (FONT_STACKS).
    """
    custom_fonts = custom_fonts or {}
    if clave in custom_fonts:
        nombre = custom_fonts[clave]["name"]
        return f"'{nombre}', 'Segoe UI', sans-serif"
    return FONT_STACKS.get(clave, FONT_STACKS["segoe"])


def _font_faces_css(custom_fonts: dict | None = None) -> str:
    """Genera los bloques @font-face para todas las fuentes personalizadas
    cargadas, para que WeasyPrint pueda usarlas en el PDF."""
    if not custom_fonts:
        return ""
    bloques = []
    for datos in custom_fonts.values():
        nombre = datos["name"]
        if datos.get("regular_path"):
            uri = Path(datos["regular_path"]).resolve().as_uri()
            bloques.append(f"""
@font-face {{
    font-family: '{nombre}';
    src: url('{uri}');
    font-weight: 400;
}}""")
        if datos.get("bold_path"):
            uri = Path(datos["bold_path"]).resolve().as_uri()
            bloques.append(f"""
@font-face {{
    font-family: '{nombre}';
    src: url('{uri}');
    font-weight: 700;
}}""")
    return "\n".join(bloques)


def _img_b64(path: Path) -> str:
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    ext = path.suffix.lower().replace(".", "")
    mime = "jpeg" if ext in ("jpg", "jpeg") else "png"
    return f"data:image/{mime};base64,{data}"


def _img_uri(source: str) -> str:
    """Retorna data-URI desde un path de archivo o desde un data-URI existente."""
    if not source:
        return ""
    if source.startswith("data:"):
        # Ya es data-URI — lo retorna tal cual
        # SVG como data-URI: WeasyPrint requiere que sea base64, no texto plano
        if "image/svg" in source and ";base64," not in source:
            # Convertir SVG text URI a base64
            try:
                svg_text = source.split(",", 1)[1]
                import urllib.parse
                svg_decoded = urllib.parse.unquote(svg_text)
                b64 = base64.b64encode(svg_decoded.encode()).decode()
                return f"data:image/svg+xml;base64,{b64}"
            except Exception:
                pass
        return source
    try:
        path = Path(source)
        with open(path, "rb") as f:
            raw = f.read()
        ext  = path.suffix.lower().replace(".", "")
        mime = {"svg": "image/svg+xml", "jpg": "image/jpeg",
                "jpeg": "image/jpeg", "png": "image/png"}.get(ext, "image/png")
        b64  = base64.b64encode(raw).decode()
        return f"data:{mime};base64,{b64}"
    except Exception:
        return ""


def _luminance(hex_color: str) -> float:
    """Retorna luminancia relativa 0-1 (0=negro, 1=blanco)."""
    try:
        h = hex_color.lstrip('#')
        r, g, b = int(h[0:2],16)/255, int(h[2:4],16)/255, int(h[4:6],16)/255
        def lin(c): return c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4
        return 0.2126*lin(r) + 0.7152*lin(g) + 0.0722*lin(b)
    except Exception:
        return 0.5

def _css_base(company: dict = None) -> str:

    portada_path = BASE_PORTADA
    interior_path = BASE_INTERIOR
    
    primary_color   = "#155FCF"
    secondary_color = "#8EE3C8"

    if company:

        primary_color = (
            company.get("primary_color")
            or primary_color
        )

        secondary_color = (
            company.get("secondary_color")
            or secondary_color
        )

    company = company or {}
    custom_fonts = company.get("_custom_fonts") or {}

    # Color para el contenido interior (cuerpo, tablas, notas al pie — SIEMPRE
    # sobre fondo blanco): prioriza cuerpo.color, luego content_color de BD,
    # y como último recurso calcula por luminancia de primary_color.
    # IMPORTANTE: nunca usar banner.text_color aquí — ese color está pensado
    # para contrastar contra el FONDO DEL BANNER (que puede ser oscuro), no
    # contra la página blanca del interior. Confundir ambos deja el texto
    # del cuerpo invisible cuando el banner usa texto blanco (ej. Atcom).
    _pc = company.get("portada_config") or {}
    _cuerpo_cfg_temp = _pc.get("cuerpo") or {}
    explicit_content = _cuerpo_cfg_temp.get("color") or company.get("content_color")
    if explicit_content:
        content_color = explicit_content
    elif _luminance(primary_color) > 0.5:
        content_color = "#1A2B5F"
    else:
        content_color = primary_color

    # Color del texto DEL BANNER específicamente (puede ser blanco sobre un
    # banner oscuro) — variable separada de content_color a propósito.
    banner_text_color = (
        (_pc.get("banner") or {}).get("text_color")
        or content_color
    )

    # secondary_color: puede venir de portada_config.banner.bg_color
    _banner_bg = (_pc.get("banner") or {}).get("bg_color")
    if _banner_bg:
        secondary_color = _banner_bg

    # Tipografía de portada desde portada_config (ya extraída en layout)
    # Tipografía de banner y cuerpo desde portada_config
    _banner_cfg = _pc.get("banner") or {}
    _cuerpo_cfg = _pc.get("cuerpo") or {}
    banner_size      = _banner_cfg.get("size",    26)
    banner_weight    = _banner_cfg.get("weight",  700)
    banner_font      = _font_stack(_banner_cfg.get("font", "segoe"), custom_fonts)
    banner_line_height = _banner_cfg.get("line_height", 1.1)
    banner_y_pct     = _banner_cfg.get("y_start", 45)   # % desde top de la página interior
    cuerpo_size      = _cuerpo_cfg.get("size",    10.5)
    cuerpo_weight    = _cuerpo_cfg.get("weight",  400)
    cuerpo_font      = _font_stack(_cuerpo_cfg.get("font", "segoe"), custom_fonts)
    cuerpo_line_height = _cuerpo_cfg.get("line_height", 1.55)
    cuerpo_y_pct     = _cuerpo_cfg.get("y_start", 75)   # % desde top de la página interior
    cuerpo_x_mm      = _cuerpo_cfg.get("x_start", 38)   # mm desde la izquierda
    # Convertir % a mm (página interior = 297mm)
    # Mapear y_start% al rango real del área de contenido interior (45mm-270mm)
    _CONTENT_START = 45   # mm desde donde empieza el área útil
    _CONTENT_END   = 270  # mm hasta donde termina el área útil  
    _CONTENT_RANGE = _CONTENT_END - _CONTENT_START  # 225mm
    banner_top_mm = round((banner_y_pct / 100) * 280, 1)
    cuerpo_top_mm = round((cuerpo_y_pct  / 100) * 280, 1)


    if company.get("portada"):
        portada_path = Path(company["portada"])

    if company.get("interior"):
        interior_path = Path(company["interior"])

    portada_uri = (
        _img_b64(portada_path)
        if portada_path.exists()
        else ""
    )

    interior_uri = (
        _img_b64(interior_path)
        if interior_path.exists()
        else ""
    )
    
    layout = company.get("portada_config") or {}

    # Valores por defecto cuando portada_config está vacío (empresa nueva)
    _DEFAULT = {
        "titulo":       {"x": 28, "y": 148, "size": 34, "weight": 700, "align": "left"},
        "objetivo":     {"x": 28, "y": 210, "size": 11, "weight": 400, "align": "left"},
        "logo_cliente": {"x": 28, "y": 248},
    }
    def _get(key, field, default):
        val = layout.get(key, {}).get(field)
        return val if val is not None else _DEFAULT[key].get(field, default)

    titulo_x      = max(0,  _get("titulo",       "x",      28))
    titulo_y      = max(5,  _get("titulo",       "y",      148))  # mínimo 5mm desde arriba
    titulo_size   = _get("titulo",       "size",   34)
    titulo_weight = _get("titulo",       "weight", 700)
    titulo_align  = _get("titulo",       "align",  "left")
    titulo_width  = _get("titulo",       "width",  150)
    titulo_font        = _font_stack(_get("titulo", "font", "segoe"), custom_fonts)
    titulo_line_height = _get("titulo", "line_height", 1.15)

    objetivo_x      = max(0,  _get("objetivo",   "x",      28))
    objetivo_y      = max(10, _get("objetivo",   "y",      210))  # mínimo 10mm
    objetivo_size   = _get("objetivo",   "size",   11)
    objetivo_weight = _get("objetivo",   "weight", 400)
    objetivo_align  = _get("objetivo",   "align",  "left")
    objetivo_font        = _font_stack(_get("objetivo", "font", "segoe"), custom_fonts)
    objetivo_line_height = _get("objetivo", "line_height", 1.4)

    logo_x = _get("logo_cliente", "x", 28)
    logo_y = _get("logo_cliente", "y", 248)
    logo_w = _get("logo_cliente", "width",  60)
    logo_h = _get("logo_cliente", "height", 34)

    return f"""
{_font_faces_css(custom_fonts)}

/* ── Tipografía corporativa ──────────────────────────────────────────────
   Century Gothic  → logotipo CP (en imagen base, no en HTML)
   Segoe UI        → TODO el texto del documento
   Times New Roman → exclusivamente la cita entrecomillada (Introducción)
──────────────────────────────────────────────────────────────────────── */
@page portada {{
    size: 210mm 297mm;
    margin: 0;
    background-image: url('{portada_uri}');
    background-size: 100% 100%;
    background-repeat: no-repeat;
}}

@page interior {{
    size: 210mm 297mm;
    margin: 0;
    background-image: url('{interior_uri}');
    background-size: 100% 100%;
    background-repeat: no-repeat;
}}
* {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}}
body {{
    font-family: 'Segoe UI', 'Segoe UI Variable', 'Trebuchet MS', Arial, Helvetica, sans-serif;
    color: {primary_color};
    font-size: 10.5pt;
}}

/* ═══════════════════════════════════════════
   PORTADA — position:absolute está bien aquí
   porque la portada es siempre 1 página fija
═══════════════════════════════════════════ */
.page-portada {{
    page: portada;
    width: 210mm;
    height: 297mm;
    position: relative;
    page-break-after: always;
}}
.portada-content {{
    position: absolute;
    left:  21mm;
    top:   41.8mm;
    width: 140mm;
}}

/* Portada título: Segoe UI Bold, 34pt — reducido para evitar overflow con títulos largos */
.portada-titulo {{
    position:absolute;
    left:{titulo_x}mm;
    top:{titulo_y}mm;
    max-width: {titulo_width}mm;
    font-family:   {titulo_font};
    font-size:     {titulo_size}pt;
    font-weight:   {titulo_weight};
    color:         {primary_color};
    line-height:   {titulo_line_height};
    text-align:    {titulo_align};
    margin-bottom: 0;
}}
/* "Preparado para:": posición absoluta medida del PDF original
   y=336.5pt = 118.8mm desde top página
   top del content = 41.8mm → margin-top = 118.8 - 41.8 = 77mm */
.portada-prep-label {{
    font-family:   'Segoe UI', 'Segoe UI Variable', Arial, sans-serif;
    font-size:     11pt;
    font-weight:   700;
    color:         {primary_color};
    margin-top:    77mm;
    margin-bottom: 3mm;
}}
.portada-cliente-nombre {{
    font-family:   'Segoe UI', 'Segoe UI Variable', Arial, sans-serif;
    font-size:     13pt;
    font-weight:   700;
    color:         {primary_color};
    margin-bottom: 6mm;
    line-height:   1.3;
}}
.portada-objetivo {{
    position: absolute;
    left: {objetivo_x}mm;
    top: {objetivo_y}mm;
    max-width: 120mm;
    font-family: {objetivo_font};
    font-size: {objetivo_size}pt;
    font-weight: {objetivo_weight};
    line-height: {objetivo_line_height};
    text-align: {objetivo_align};
    color: {primary_color};
}}
/* Logo cliente — centrado en círculo verde menta
   Centro círculo: x=163.4mm, y=250.4mm, radio≈56mm */
.portada-elaborado {{
    position: absolute;
    left: {logo_x}mm;
    top: {logo_y}mm;
    width: {logo_w}mm;
    font-family:     'Segoe UI', 'Segoe UI Variable', Arial, sans-serif;
    font-size:       10pt;
    font-weight:     700;
    color:           {primary_color};
    text-align:      center;
    display:         flex;
    flex-direction:  column;
    align-items:     center;
    justify-content: center;
    gap:             3mm;
}}

/* ═══════════════════════════════════════════
   PÁGINAS INTERIORES
   Cada .page-interior = 1 página con fondo base_interior.png
   El contenido fluye dentro del área blanca medida:
     left=43.6mm, top=86mm, width=148mm
   WeasyPrint crea páginas adicionales automáticamente
   cuando el div desborda (no hay height fijo).
═══════════════════════════════════════════ */
.page-interior {{
    page: interior;
    position: relative;
    width:  210mm;
    height: 297mm;
    page-break-after: always;
}}
.page-interior:last-child {{
    page-break-after: avoid;
}}
.interior-content {{
    position: absolute;
    left:    43.6mm;
    top:     86mm;
    width:   148mm;
}}

/* ═══════════════════════════════════════════
   PÁGINAS CON BANNER — bloques absolutamente independientes
   
   Alcance (pág 3):
     banner:  left=38mm, top=50mm  (y real=52.9mm)
     body:    left=38mm, top=119mm (y real=119mm — DEBAJO de la foto)
   
   Centro de Costos (pág 7):
     banner:  left=38mm, top=73mm  (y real=75.7mm)
     body:    left=38mm, top=99mm  (y real=98.9mm)
═══════════════════════════════════════════ */

/* Posición del banner (bloque verde con título) */
/* Banner título — posicionado absolutamente con dimensiones exactas */
.banner-titulo {{
    font-family:   {banner_font};
    background:    {secondary_color};
    color:         {banner_text_color};
    font-size:     {banner_size}pt;
    font-weight:   {banner_weight};
    padding:       3mm 8mm;
    display:       block;
    width:         160mm;
    line-height:   {banner_line_height};
    position:      absolute;
    left:          32mm;
    top:           {banner_top_mm}mm;
}}
.banner-titulo.banner-alcance-pos {{
    top: {banner_top_mm}mm;
}}
.banner-titulo.banner-costos-pos {{
    top: {banner_top_mm}mm;
}}

/* Body independiente del banner — posicionado exactamente donde empieza el texto real */
.banner-body-alcance {{
    position: absolute;
    left:     {cuerpo_x_mm}mm;
    top:      {cuerpo_top_mm}mm;
    width:    {round(190 - cuerpo_x_mm)}mm;
}}
.banner-body-costos {{
    position: absolute;
    left:     {cuerpo_x_mm}mm;
    top:      {cuerpo_top_mm}mm;
    width:    158mm;
}}

/* ═══════════════════════════════════════════
   TIPOGRAFÍA INTERIOR — Segoe UI en toda la jerarquía
═══════════════════════════════════════════ */

/* H1 — Títulos principales de sección (Introducción, Alcance, etc.)
   Fuente: Segoe UI Bold, 26pt */
h1 {{
    font-family:   'Segoe UI', 'Segoe UI Variable', Arial, sans-serif;
    font-size:     26pt;
    font-weight:   700;
    color:         {content_color};
    margin-bottom: 3mm;
    line-height:   1.15;
}}

/* H2 — Subtítulos de sección (Valor Estratégico, etc.)
   Fuente: Segoe UI Bold, 14pt */
h2 {{
    font-family:   'Segoe UI', 'Segoe UI Variable', Arial, sans-serif;
    font-size:     14pt;
    font-weight:   700;
    color:         {content_color};
    margin-top:    5mm;
    margin-bottom: 2mm;
    line-height:   1.25;
}}

/* H3 — Subtítulos secundarios (Antecedente Crítico, numerados 1. 2. 3.)
   Fuente: Segoe UI Bold, 11pt */
h3 {{
    font-family:   'Segoe UI', 'Segoe UI Variable', Arial, sans-serif;
    font-size:     11pt;
    font-weight:   700;
    color:         {content_color};
    margin-top:    3mm;
    margin-bottom: 1.5mm;
}}

.hr {{
    border:         none;
    border-top:     0.8pt solid {content_color};
    margin-bottom:  3mm;
    margin-top:     0.5mm;
}}

/* Body — párrafos de cuerpo general
   Fuente: Segoe UI Regular, 10.5pt, justificado */
p {{
    font-family:   {cuerpo_font};
    font-size:     {cuerpo_size}pt;
    font-weight:   {cuerpo_weight};
    color:         {content_color};
    line-height:   {cuerpo_line_height};
    text-align:    justify;
    margin-bottom: 3mm;
}}

/* Cita entrecomillada — ÚNICA excepción tipográfica
   Fuente: Times New Roman Bold Italic, 10.5pt
   Según análisis: "cambia de familia tipográfica a una fuente con serifa
   utilizada específicamente para denotar declaración textual o misión literal" */
.cita {{
    font-family:   'Times New Roman', 'Times', Georgia, serif;
    font-size:     10.5pt;
    font-weight:   700;
    font-style:    italic;
    color:         {content_color};
    text-align:    justify;
    line-height:   1.6;
    margin-bottom: 3mm;
    margin-top:    2mm;
}}

/* Viñetas — Segoe UI Regular, concepto inicial en Bold (via HTML <strong>) */
ul {{
    padding-left:  5mm;
    margin-bottom: 3mm;
}}
ul li {{
    font-family:   'Segoe UI', 'Segoe UI Variable', Arial, sans-serif;
    font-size:     10.5pt;
    font-weight:   400;
    color:         {content_color};
    line-height:   1.55;
    margin-bottom: 1mm;
    text-align:    justify;
}}
ul li strong {{
    font-weight: 700;
}}

/* ═══════════════════════════════════════════
   FIRMA — Segoe UI, centrada
═══════════════════════════════════════════ */
.firma-bloque {{
    margin-top:    18mm;
    text-align:    center;
    padding-top:   0;
    width:         60mm;
    margin-left:   auto;
    margin-right:  auto;
}}
/* Nombre firma: Segoe UI Bold */
.firma-nombre {{
    font-family:   'Segoe UI', 'Segoe UI Variable', Arial, sans-serif;
    font-size:     10.5pt;
    font-weight:   700;
    color:         {content_color};
    line-height:   1.5;
}}
/* Cargo firma: Segoe UI Regular */
.firma-cargo {{
    font-family:   'Segoe UI', 'Segoe UI Variable', Arial, sans-serif;
    font-size:     10.5pt;
    font-weight:   400;
    color:         {content_color};
    line-height:   1.5;
}}

/* ═══════════════════════════════════════════
   LISTA DE SERVICIOS — formato compacto
   Igual que propuesta_real: categoría en H2, servicios en lista
   con nombre en bold seguido de descripción corta inline
═══════════════════════════════════════════ */
.srv-lista {{
    padding-left:  5mm;
    margin-top:    1mm;
    margin-bottom: 4mm;
    list-style:    none;
}}
.srv-lista > li {{
    font-family:   'Segoe UI', 'Segoe UI Variable', Arial, sans-serif;
    font-size:     10pt;
    font-weight:   400;
    color:         {content_color};
    line-height:   1.5;
    margin-bottom: 1.5mm;
    text-align:    justify;
}}
.srv-lista > li::before {{
    content: "• ";
    font-weight: 700;
}}
.srv-lista li strong {{
    font-weight: 700;
}}
/* Intro de servicio — párrafo antes de las viñetas */
.srv-intro {{
    font-family:   'Segoe UI', 'Segoe UI Variable', Arial, sans-serif;
    font-size:     10pt;
    color:         {content_color};
    line-height:   1.5;
    text-align:    justify;
    margin-bottom: 2mm;
}}
/* Sección dentro del servicio — título de fase/bloque */
.srv-seccion-titulo {{
    font-family:   'Segoe UI', 'Segoe UI Variable', Arial, sans-serif;
    font-size:     10.5pt;
    font-weight:   700;
    color:         {content_color};
    margin-top:    3mm;
    margin-bottom: 1mm;
}}
/* Lista principal de sección */
.srv-seccion-lista {{
    padding-left:  5mm;
    margin-top:    0;
    margin-bottom: 2mm;
    list-style:    none;
}}
.srv-seccion-lista > li {{
    font-family:   'Segoe UI', 'Segoe UI Variable', Arial, sans-serif;
    font-size:     10pt;
    font-weight:   700;
    color:         {content_color};
    line-height:   1.5;
    margin-bottom: 1mm;
}}
.srv-seccion-lista > li::before {{
    content: "▸ ";
    font-weight: 700;
}}
/* Sub-lista dentro de cada item de sección */
.srv-sub-lista {{
    padding-left:  6mm;
    margin-top:    0.5mm;
    margin-bottom: 1mm;
    list-style:    none;
}}
.srv-sub-lista > li {{
    font-family:   'Segoe UI', 'Segoe UI Variable', Arial, sans-serif;
    font-size:     9.5pt;
    font-weight:   400;
    color:         {content_color};
    line-height:   1.45;
    margin-bottom: 0.8mm;
    text-align:    justify;
}}
.srv-sub-lista > li::before {{
    content: "– ";
}}

/* ═══════════════════════════════════════════
   TABLA COSTOS
═══════════════════════════════════════════ */
.tabla-costos {{
    width:           100%;
    border-collapse: collapse;
    margin-bottom:   4mm;
    border:          0.5pt solid #CCCCCC;
}}
/* Tabla costos: th=Segoe UI Bold, td=Segoe UI Regular */
.tabla-costos th {{
    font-family:   'Segoe UI', 'Segoe UI Variable', Arial, sans-serif;
    background:    {content_color};
    color:         white;
    font-size:     10pt;
    font-weight:   700;
    padding:       2.5mm 3mm;
    text-align:    left;
    border:        0.5pt solid #CCCCCC;
}}
.tabla-costos th.right {{ text-align: center; }}
.tabla-costos td {{
    font-family:   'Segoe UI', 'Segoe UI Variable', Arial, sans-serif;
    font-size:     9pt;
    font-weight:   400;
    color:         {content_color};
    padding:       2mm 3mm;
    border:        0.5pt solid #CCCCCC;
}}
.tabla-costos td.right {{ text-align: center; }}
.tabla-costos tr.cat-row td {{
    background:  #EBF3FF;
    font-weight: bold;
    font-size:   9.5pt;
}}
.tabla-costos tr.srv-row:nth-child(odd) td  {{ background: white; }}
.tabla-costos tr.srv-row:nth-child(even) td {{ background: #F5F9FF; }}
.tabla-costos tr.total-row td {{
    background:  {content_color};
    color:       white;
    font-weight: bold;
    font-size:   10pt;
    padding:     3mm;
}}
.tabla-costos tr.total-row td.right {{ text-align: center; }}

/* ═══════════════════════════════════════════
   TABLA PLANES DE CONTRATACIÓN
═══════════════════════════════════════════ */
.tabla-planes {{
    width:           100%;
    border-collapse: collapse;
    margin-bottom:   4mm;
    margin-top:      2mm;
    border:          0.5pt solid #CCCCCC;
}}
.tabla-planes th {{
    font-family:   'Segoe UI', 'Segoe UI Variable', Arial, sans-serif;
    background:    {content_color};
    color:         white;
    font-size:     10pt;
    font-weight:   700;
    padding:       2.5mm 3mm;
    text-align:    center;
    border:        0.5pt solid #CCCCCC;
}}
.tabla-planes td {{
    font-family:   'Segoe UI', 'Segoe UI Variable', Arial, sans-serif;
    font-size:     9.5pt;
    font-weight:   400;
    color:         {content_color};
    padding:       3mm;
    text-align:    center;
    border:        0.5pt solid #CCCCCC;
}}
.tabla-planes tr.plan-row:nth-child(odd) td  {{ background: white; }}
.tabla-planes tr.plan-row:nth-child(even) td {{ background: #F5F9FF; }}
.tabla-planes tr.plan-row td.plazo {{
    font-weight: 700;
    text-align:  left;
}}
.tabla-planes tr.plan-row td.precio-final {{
    font-weight: 700;
    font-size:   10.5pt;
}}
.tabla-planes tr.plan-recomendado td {{
    background:  #1D9E75 !important;
    color:       white !important;
    font-weight: 700;
}}
.tabla-planes tr.plan-recomendado td.precio-final {{
    font-size: 11pt;
}}
.plan-badge {{
    display:       inline-block;
    background:    white;
    color:         #1D9E75;
    font-size:     7.5pt;
    font-weight:   700;
    padding:       0.8mm 2.5mm;
    border-radius: 3mm;
    margin-left:   2mm;
    vertical-align: middle;
}}

/* ═══════════════════════════════════════════
   TABLA MATRIZ DE VALOR
═══════════════════════════════════════════ */
.tabla-matriz {{
    width:           100%;
    border-collapse: collapse;
    margin-bottom:   4mm;
    margin-top:      2mm;
    font-size:       9pt;
    border:          0.5pt solid #CCCCCC;
}}
/* Tabla matriz: th=Segoe UI Bold, td=Segoe UI Regular */
.tabla-matriz th {{
    font-family:   'Segoe UI', 'Segoe UI Variable', Arial, sans-serif;
    background:    {content_color};
    color:         white;
    padding:       2mm 2.5mm;
    text-align:    left;
    font-weight:   700;
    border:        0.5pt solid #CCCCCC;
}}
.tabla-matriz td {{
    font-family:   'Segoe UI', 'Segoe UI Variable', Arial, sans-serif;
    font-weight:   400;
    color:         {content_color};
    padding:       2.5mm 2.5mm;
    border:        0.5pt solid #CCCCCC;
    vertical-align: top;
    line-height:   1.4;
}}
.tabla-matriz tr:nth-child(even) td {{ background: #EBF3FF; }}
.tabla-matriz tr:nth-child(odd)  td {{ background: white; }}

/* ═══════════════════════════════════════════
   CONDICIONES
═══════════════════════════════════════════ */
/* Condiciones: Segoe UI Regular; subtítulos en Bold via HTML <strong> */
.condicion-linea {{
    font-family:   'Segoe UI', 'Segoe UI Variable', Arial, sans-serif;
    font-size:     10pt;
    font-weight:   400;
    color:         {content_color};
    line-height:   1.7;
}}
/* Nota pie: Segoe UI Italic */
.nota-pie {{
    font-family:   'Segoe UI', 'Segoe UI Variable', Arial, sans-serif;
    font-size:     8.5pt;
    font-weight:   400;
    font-style:    italic;
    color:         {content_color};
    text-align:    center;
    margin-top:    3mm;
}}
"""


# ══════════════════════════════════════════════════════════════════════════════
# SECCIONES HTML
# ══════════════════════════════════════════════════════════════════════════════

def _page_std(contenido_html: str) -> str:
    """Página interior estándar."""
    return f'<div class="page-interior"><div class="interior-content">{contenido_html}</div></div>'


def _pages(secciones: list) -> str:
    """Une múltiples secciones cada una en su propia página."""
    return "".join(_page_std(s) for s in secciones)


def _page_banner(titulo_banner: str, contenido_html: str) -> str:
    """Página Alcance: banner a top=50mm, body a top=119mm (bajo la foto)."""
    return f'''<div class="page-interior">
  <div class="banner-titulo banner-alcance-pos">{titulo_banner}</div>
  <div class="banner-body-alcance">
    {contenido_html}
  </div>
</div>'''


def _page_banner_costos(titulo_banner: str, contenido_html: str) -> str:
    """Página Centro de Costos: banner a top=73mm, body a top=99mm."""
    return f'''<div class="page-interior">
  <div class="banner-titulo banner-costos-pos">{titulo_banner}</div>
  <div class="banner-body-costos">
    {contenido_html}
  </div>
</div>'''


def sec_portada(data: dict) -> str:

    titulo  = data.get("titulo_proyecto", "")
    para    = data.get("preparado_para", "")
    obj     = data.get("objetivo", "")

    # ─────────────────────────────
    # Empresa emisora
    # ─────────────────────────────

    company = data.get("company", {})

    primary_color = (
        company.get("primary_color")
        or "#155FCF"
    )

    empresa_html = ""

    # ─────────────────────────────
    # Logo cliente
    # ─────────────────────────────

    logo_cliente = _img_uri(
        data.get("logo_cliente") or ""
    )

    # Tamaño del logo desde portada_config
    _pc_logo = (company.get("portada_config") or {}).get("logo_cliente") or {}
    logo_w = _pc_logo.get("width",  60)
    logo_h = _pc_logo.get("height", 34)

    cliente_html = (

        f'''
        <div class="portada-elaborado">

            <div style="
                font-size:9pt;
                font-weight:700;
                color:{primary_color};
                letter-spacing:0.5pt;
            ">
                Elaborado para:
            </div>

            <img src="{logo_cliente}"
                style="
                max-width:{logo_w}mm;
                max-height:{logo_h}mm;
                object-fit:contain;
                ">
        </div>
        '''

        if logo_cliente else ""
    )



    return f'''
    <section class="page-portada">

        <h1 class="portada-titulo">
            {titulo}
        </h1>

        <p class="portada-objetivo">
            {obj}
        </p>

        <div class="portada-content">

        </div>

        {cliente_html}

    </section>
    '''


def sec_introduccion(data: dict) -> str:
    html = f'''
<p>{data.get("introduccion", "")}</p>
<p class="cita">"{data.get("frase_clave", "")}"</p>
<p>{data.get("cierre_intro", "")}</p>
<div class="firma-bloque">
  <div class="firma-cargo">________________________</div>
  <div class="firma-nombre">Andrés Barrientos Cisternas</div>
  <div class="firma-cargo">CTO / CYBERPROTECTION.CL</div>
</div>'''
    return _page_banner("Introducción", html)


def sec_alcance(data: dict) -> str:
    html = f'<p>{data.get("alcance_intro", "")}</p>'
    if data.get("antecedente_titulo"):
        html += f'<h3>{data["antecedente_titulo"]}</h3>'
        for par in (data.get("antecedente_descripcion") or "").split("\n\n"):
            if par.strip():
                html += f"<p>{par.strip()}</p>"
    for b in (data.get("antecedente_bullets") or []):
        html += f"<ul><li>{b}</li></ul>"
    return _page_banner("Alcance", html)


def _render_desc_estructurada(desc_obj: dict) -> str:
    """
    Renderiza una descripción estructurada (JSON) como HTML con viñetas.
    Formato esperado:
    {
      "intro": "Texto introductorio...",
      "secciones": [
        {
          "titulo": "Fases del Servicio",
          "items": [
            {
              "label": "Fase 1: Nombre",
              "subitems": ["actividad 1", "actividad 2"]
            },
            {"label": "Entregable sin subitems"}
          ]
        }
      ]
    }
    """
    html = ""
    intro = desc_obj.get("intro", "")
    if intro:
        html += f'<p class="srv-intro">{intro}</p>'

    for seccion in desc_obj.get("secciones", []):
        titulo = seccion.get("titulo", "")
        if titulo:
            html += f'<p class="srv-seccion-titulo">{titulo}</p>'
        items = seccion.get("items", [])
        if items:
            html += '<ul class="srv-seccion-lista">'
            for item in items:
                label = item.get("label", "")
                subitems = item.get("subitems", [])
                if subitems:
                    html += f'<li><strong>{label}</strong>'
                    html += '<ul class="srv-sub-lista">'
                    for sub in subitems:
                        html += f'<li>{sub}</li>'
                    html += '</ul></li>'
                else:
                    html += f'<li><strong>{label}</strong></li>'
            html += '</ul>'
    return html


def _estimar_alto_estructurado(desc_obj: dict, chars_por_linea: int) -> int:
    """Estima unidades de altura de una descripción estructurada."""
    total = 0
    intro = desc_obj.get("intro", "")
    if intro:
        total += max(1, -(-len(intro) // chars_por_linea)) + 1

    for seccion in desc_obj.get("secciones", []):
        if seccion.get("titulo"):
            total += 2
        for item in seccion.get("items", []):
            total += 1  # label
            total += len(item.get("subitems", []))  # subitems
        total += 1  # margen entre secciones
    return max(total, 2)


def _parse_texto_estructurado(texto: str, nombre_srv: str = "") -> dict:
    """Convierte texto con numeraciones/guiones a dict estructurado para renderizar con viñetas."""
    import re
    if not texto or len(texto) < 50:
        return None
    lineas = [l.strip() for l in texto.split("\n") if l.strip()]
    if len(lineas) < 3:
        return None
    tiene_num = sum(1 for l in lineas if re.match(r"^\d+\.|^Fase\s+\d|^Etapa\s+\d|^Paso\s+\d", l, re.I)) >= 2
    tiene_gui = sum(1 for l in lineas if l.startswith(("-","–","•"))) >= 3
    if not tiene_num and not tiene_gui:
        return None
    intro_lines, resto = [], list(lineas)
    for l in lineas:
        if re.match(r"^\d+\.|^Fase\s+\d|^Etapa\s+\d|^Paso\s+\d|^[-–•]", l, re.I):
            break
        intro_lines.append(l); resto = resto[1:]
    intro = " ".join(intro_lines).strip()
    items, cur_label, cur_subs = [], None, []
    for l in resto:
        m = re.match(r"^(\d+\.|Fase\s+\d+:?|Etapa\s+\d+:?|Paso\s+\d+:?)\s*(.+)", l, re.I)
        if m:
            if cur_label: items.append({"label": cur_label, "subitems": cur_subs})
            cur_label, cur_subs = m.group(2).strip(), []
        elif l.startswith(("-","–","•")) and cur_label:
            sub = re.sub(r"^[-–•]\s*", "", l).strip()
            if sub: cur_subs.append(sub)
        elif not cur_label and (l.startswith(("-","–","•")) or tiene_gui):
            sub = re.sub(r"^[-–•]\s*", "", l).strip()
            if sub: items.append({"label": sub, "subitems": []})
    if cur_label: items.append({"label": cur_label, "subitems": cur_subs})
    if not items:
        return None
    return {"intro": intro or nombre_srv, "secciones": [{"titulo": "Componentes del Servicio", "items": items}]}


def _srv_bloques(srv: dict, chars_por_linea: int, lineas_por_pagina: int) -> list:
    """
    Genera uno o más bloques HTML para un servicio.
    Soporta descripción como:
      - str simple → paginación por chunks de texto
      - dict estructurado → renderizado con viñetas y secciones
    Cada bloque es (html, unidades_alto, es_continuacion).
    """
    nombre = srv.get("nombre", "")

    # ── Descripción estructurada (dict con intro + secciones) ──
    desc_raw = srv.get("descripcion", "")
    if isinstance(desc_raw, dict):
        alto = _estimar_alto_estructurado(desc_raw, chars_por_linea)
        contenido = _render_desc_estructurada(desc_raw)
        html = f'<p class="srv-seccion-titulo">{nombre}</p>{contenido}'
        # Si cabe en una página, retornar como bloque único
        if alto <= lineas_por_pagina:
            return [(html, alto, False)]
        # Si no cabe, dividir secciones en páginas (una sección por página como mínimo)
        bloques = []
        intro = desc_raw.get("intro", "")
        secciones = desc_raw.get("secciones", [])
        pagina_html = f'<p class="srv-seccion-titulo">{nombre}</p>'
        if intro:
            pagina_html += f'<p class="srv-intro">{intro}</p>'
        unidades = 2 + (max(1, -(-len(intro) // chars_por_linea)) + 1 if intro else 0)
        primera = True

        for seccion in secciones:
            alto_sec = 2  # titulo
            for item in seccion.get("items", []):
                alto_sec += 1 + len(item.get("subitems", []))
            alto_sec += 1

            if not primera and (unidades + alto_sec) > lineas_por_pagina:
                bloques.append((pagina_html, unidades, not primera))
                pagina_html = f'<p class="srv-seccion-titulo">{nombre} (cont.)</p>'
                unidades = 2

            titulo = seccion.get("titulo", "")
            sec_html = ""
            if titulo:
                sec_html += f'<p class="srv-seccion-titulo">{titulo}</p>'
            items = seccion.get("items", [])
            if items:
                sec_html += '<ul class="srv-seccion-lista">'
                for item in items:
                    label = item.get("label", "")
                    subitems = item.get("subitems", [])
                    if subitems:
                        sec_html += f'<li><strong>{label}</strong><ul class="srv-sub-lista">'
                        for sub in subitems:
                            sec_html += f'<li>{sub}</li>'
                        sec_html += '</ul></li>'
                    else:
                        sec_html += f'<li><strong>{label}</strong></li>'
                sec_html += '</ul>'

            pagina_html += sec_html
            unidades += alto_sec
            primera = False

        bloques.append((pagina_html, unidades, True))
        return bloques

    # ── Intentar parsear texto estructurado como fallback ──
    desc_raw_str = str(desc_raw).strip() if desc_raw else ""
    parsed = _parse_texto_estructurado(desc_raw_str, srv.get("nombre", ""))
    if parsed:
        alto = _estimar_alto_estructurado(parsed, chars_por_linea)
        contenido = _render_desc_estructurada(parsed)
        html = f'<p class="srv-seccion-titulo">{nombre}</p>{contenido}'
        if alto <= lineas_por_pagina:
            return [(html, alto, False)]
        return [(html, lineas_por_pagina, False)]  # simplificado para textos muy largos

    # ── Descripción como texto plano ──
    desc = ""
    if desc_raw:
        desc = str(desc_raw).split("|")[0].strip()
    elif srv.get("bullets"):
        b0 = srv["bullets"][0] if srv["bullets"] else ""
        desc = b0.replace("Descripción: ", "").strip()

    if not desc:
        lineas = max(1, -(-len(nombre) // chars_por_linea))
        return [(f'<li><strong>{nombre}</strong></li>', lineas, False)]

    prefijo = f"{nombre}: "
    chars_primer_bloque = max(chars_por_linea - len(prefijo), 20) + (chars_por_linea * (lineas_por_pagina - 1))

    if len(desc) <= chars_primer_bloque:
        texto_total = len(prefijo) + len(desc)
        lineas = max(1, -(-texto_total // chars_por_linea))
        return [(f'<li><strong>{nombre}:</strong> {desc}</li>', lineas, False)]

    bloques = []
    corte = desc.rfind(" ", 0, chars_primer_bloque)
    if corte == -1:
        corte = chars_primer_bloque
    primera_desc = desc[:corte].strip()
    resto = desc[corte:].strip()

    texto_total = len(prefijo) + len(primera_desc)
    lineas = max(1, -(-texto_total // chars_por_linea))
    bloques.append((f'<li><strong>{nombre}:</strong> {primera_desc}</li>', lineas, False))

    chars_bloque_cont = chars_por_linea * lineas_por_pagina
    while resto:
        if len(resto) <= chars_bloque_cont:
            lineas = max(1, -(-len(resto) // chars_por_linea))
            bloques.append((f'<li>{resto}</li>', lineas, True))
            break
        corte = resto.rfind(" ", 0, chars_bloque_cont)
        if corte == -1:
            corte = chars_bloque_cont
        parte = resto[:corte].strip()
        resto = resto[corte:].strip()
        lineas = max(1, -(-len(parte) // chars_por_linea))
        bloques.append((f'<li>{parte}</li>', lineas, True))

    return bloques
    """
    Genera uno o más bloques HTML para un servicio.
    Si la descripción es larga la divide en chunks que caben en una página.
    Cada bloque es (html, unidades_alto, es_continuacion).
    Los bloques de continuación no repiten el nombre — texto continuo.
    """
    nombre = srv.get("nombre", "")
    desc = ""
    if srv.get("descripcion"):
        desc = srv["descripcion"].split("|")[0].strip()
    elif srv.get("bullets"):
        b0 = srv["bullets"][0] if srv["bullets"] else ""
        desc = b0.replace("Descripción: ", "").strip()

    if not desc:
        lineas = max(1, -(-len(nombre) // chars_por_linea))
        return [(f'<li><strong>{nombre}</strong></li>', lineas, False)]

    # Espacio disponible en primer bloque (descontando prefijo "Nombre: ")
    prefijo = f"{nombre}: "
    chars_primer_bloque = max(chars_por_linea - len(prefijo), 20) + (chars_por_linea * (lineas_por_pagina - 1))

    if len(desc) <= chars_primer_bloque:
        texto_total = len(prefijo) + len(desc)
        lineas = max(1, -(-texto_total // chars_por_linea))
        return [(f'<li><strong>{nombre}:</strong> {desc}</li>', lineas, False)]

    bloques = []

    # Primer bloque
    corte = desc.rfind(" ", 0, chars_primer_bloque)
    if corte == -1:
        corte = chars_primer_bloque
    primera_desc = desc[:corte].strip()
    resto = desc[corte:].strip()

    texto_total = len(prefijo) + len(primera_desc)
    lineas = max(1, -(-texto_total // chars_por_linea))
    bloques.append((f'<li><strong>{nombre}:</strong> {primera_desc}</li>', lineas, False))

    # Bloques de continuación — sin encabezado, texto continuo
    chars_bloque_cont = chars_por_linea * lineas_por_pagina
    while resto:
        if len(resto) <= chars_bloque_cont:
            lineas = max(1, -(-len(resto) // chars_por_linea))
            bloques.append((f'<li>{resto}</li>', lineas, True))
            break
        corte = resto.rfind(" ", 0, chars_bloque_cont)
        if corte == -1:
            corte = chars_bloque_cont
        parte = resto[:corte].strip()
        resto = resto[corte:].strip()
        lineas = max(1, -(-len(parte) // chars_por_linea))
        bloques.append((f'<li>{parte}</li>', lineas, True))

    return bloques


def sec_servicios(data: dict, agrupado: dict) -> str:
    """
    Divide servicios en páginas usando estimado de altura por texto.
    Soporta servicios con descripciones muy largas paginándolos en múltiples
    bloques sin encabezado repetido — el texto fluye de forma continua.

    Métricas:
      CHARS_POR_LINEA = 90   → 10pt Segoe UI en 148mm
      LINEAS_POR_PAG  = 26   → área útil por página sin encabezado
      ENCABEZADO_COSTO = 10  → h1 + hr + párrafo intro (primera página)
      CAT_HEADER_COSTO = 3   → h2 de categoría
      VALOR_EST_COSTO  = 10  → reserva para valor estratégico
    """
    CHARS_POR_LINEA  = 90
    LINEAS_POR_PAG   = 26
    ENCABEZADO_COSTO = 10
    CAT_HEADER_COSTO = 3
    VALOR_EST_COSTO  = 10

    total = sum(len(v) for v in agrupado.values())

    encabezado_html = (
        f'<p>Suite de {total} servicio{"s" if total != 1 else ""} especializados '
        f'en {len(agrupado)} área{"s" if len(agrupado) != 1 else ""} de cobertura, '
        f'diseñados para proteger integralmente su organización.</p>'
    )

    paginas        = []
    pagina_html    = encabezado_html
    unidades_usadas = ENCABEZADO_COSTO
    lista_abierta  = False
    primera_pagina = True

    def _flush():
        nonlocal pagina_html, unidades_usadas, lista_abierta
        if lista_abierta:
            pagina_html += '</ul>'
            lista_abierta = False
        paginas.append(_page_banner("Servicios Propuestos", pagina_html))
        pagina_html = ''
        unidades_usadas = 0

    def _abrir_lista():
        nonlocal lista_abierta, pagina_html
        if not lista_abierta:
            pagina_html += '<ul class="srv-lista">'
            lista_abierta = True

    def _cerrar_lista():
        nonlocal lista_abierta, pagina_html
        if lista_abierta:
            pagina_html += '</ul>'
            lista_abierta = False

    for cat, srvs in agrupado.items():
        cat_emitida = False

        for srv in srvs:
            bloques = _srv_bloques(srv, CHARS_POR_LINEA, LINEAS_POR_PAG)

            for bloque_html, bloque_cost, es_cont in bloques:
                costo_cat   = CAT_HEADER_COSTO if not cat_emitida else 0
                costo_total = bloque_cost + costo_cat

                if (unidades_usadas + costo_total) > LINEAS_POR_PAG and not primera_pagina:
                    _flush()
                    cat_emitida = False
                    costo_cat   = CAT_HEADER_COSTO

                primera_pagina = False

                if not cat_emitida:
                    _cerrar_lista()
                    pagina_html += f'<h2>{cat}</h2>'
                    unidades_usadas += CAT_HEADER_COSTO
                    cat_emitida = True

                _abrir_lista()
                pagina_html += bloque_html
                unidades_usadas += bloque_cost

    _cerrar_lista()
    paginas.append(_page_banner("Servicios Propuestos", pagina_html))

    # Valor estratégico — siempre en página propia con banner
    valor_est = data.get("valor_estrategico", "")
    if valor_est:
        paginas.append(_page_banner("Valor Estratégico", f'<p>{valor_est}</p>'))

    return "".join(paginas)


def sec_cumplimiento(data: dict) -> str:
    """Página propia: Cumplimiento Normativo."""
    cum = data.get("cumplimiento", {})
    html = f'<p><strong>{cum.get("intro", "")}</strong></p><ul>'
    for b in cum.get("bullets", []):
        html += f"<li>{b}</li>"
    html += "</ul>"
    return _page_banner("Cumplimiento Normativo", html)


def sec_matriz(data: dict) -> str:
    """Matriz de Valor — paginada en bloques de MAX_MATRIZ filas."""
    MAX_FILAS = 10
    filas = data.get("matriz_valor", [])
    if not filas:
        return _page_banner("Matriz de Valor", "")

    TH = '''<table class="tabla-matriz">
        <tr>
          <th style="width:33%">Servicio</th>
          <th style="width:34%">Beneficio Directo</th>
          <th style="width:33%">Valor Agregado</th>
        </tr>'''

    paginas = []
    for i in range(0, len(filas), MAX_FILAS):
        chunk = filas[i:i + MAX_FILAS]
        es_primera = (i == 0)
        titulo = '<p><strong>Áreas que cubre el servicio y aporta a la organización</strong></p>' if es_primera else ''
        tabla = TH
        for f in chunk:
            tabla += f'''<tr>
              <td>{f.get("servicio","")}</td>
              <td>{f.get("beneficio","")}</td>
              <td>{f.get("valor_agregado","")}</td>
            </tr>'''
        tabla += "</table>"
        paginas.append(_page_banner("Matriz de Valor", titulo + tabla))

    return "".join(paginas)


def sec_metodologia(data: dict) -> str:
    html = '<h2>4. Metodología de Trabajo</h2><div class="hr"></div>'
    
    # 1. Ciclo para la Metodología
    metodologia_lista = data.get("metodologia", [])
    if metodologia_lista:
        html += "<ul>"
        for item in metodologia_lista:
            html += f"<li>{item}</li>"
        html += "</ul>"
    
    html += '<h2>5. Diferenciadores Locales</h2><div class="hr"></div>'
    
    # 2. Ciclo para los Diferenciadores (Independiente y limpio)
    diferenciadores_lista = data.get("diferenciadores", [])
    if diferenciadores_lista:
        html += "<ul>"
        for item in diferenciadores_lista:
            html += f"<li>{item}</li>"
        html += "</ul>"
        
    return _page_banner("Metodología", html)


def sec_costos(agrupado: dict, data: dict) -> tuple:
    """Centro de Costos — paginado en bloques de 14 filas (cat+srv).
    Retorna (html_paginas, total_uf_mes)."""
    MAX_FILAS = 14
    TH = '''<table class="tabla-costos">
<tr>
  <th>Servicio</th>
  <th class="right">Costo Mensual (UF)</th>
</tr>'''

    # Construir lista plana de filas con su total acumulado
    total = 0.0
    filas = []  # lista de html strings
    for cat, srvs in agrupado.items():
        filas.append(('cat', f'<tr class="cat-row"><td>&#9632; {cat}</td><td></td></tr>'))
        for srv in srvs:
            precio = srv.get("base_price", 0)
            total += precio if isinstance(precio, (int, float)) else 0
            precio_str = f"{precio:.1f}" if isinstance(precio, (int, float)) and precio > 0 else "A convenir"
            filas.append(('srv', f'<tr class="srv-row"><td>&nbsp;&nbsp;{srv["nombre"]}</td><td class="right">{precio_str}</td></tr>'))

    total_str = f"{total:.1f} UF/mes" if total > 0 else "A convenir"
    fila_total = f'''<tr class="total-row"><td>TOTAL SUITE</td><td class="right">{total_str}</td></tr>'''

    paginas = []
    for i in range(0, len(filas), MAX_FILAS):
        chunk = filas[i:i + MAX_FILAS]
        es_primera = (i == 0)
        es_ultima  = (i + MAX_FILAS >= len(filas))

        titulo = '<h1>Centro de Costos:</h1><div class="hr"></div><p>Valores referenciales por área. Costos definitivos a confirmar en reunión de alcance.</p>' if es_primera else '<h1>Centro de Costos: </h1><div class="hr"></div>'
        tabla = TH
        for _, fila_html in chunk:
            tabla += fila_html
        if es_ultima:
            tabla += fila_total
        tabla += "</table>"
        if es_ultima and data.get("nota_costos"):
            tabla += f'<div class="nota-pie">{data["nota_costos"]}</div>'
        paginas.append(_page_banner("Centro de Costos", tabla))

    return "".join(paginas), total


def sec_planes(total_uf_mes: float, data: dict) -> str:
    """Pagina 'Planes de Contratacion' — opciones de plazo (sin descuentos).
    Solo se genera si hay un total UF/mes calculable (servicios con precio)."""
    if not total_uf_mes or total_uf_mes <= 0:
        return ""

    PLANES = [
        {"meses": 3,  "label": "Plan Flexible"},
        {"meses": 6,  "label": "Plan Semestral"},
        {"meses": 9,  "label": "Plan Extendido"},
        {"meses": 12, "label": "Plan Anual"},
    ]

    filas = []
    for plan in PLANES:
        es_recomendado = plan["meses"] == 12
        row_class = "plan-row plan-recomendado" if es_recomendado else "plan-row"
        badge = '<span class="plan-badge">Recomendado</span>' if es_recomendado else ""

        fila = (
            f'<tr class="{row_class}">'
            f'<td class="plazo">{plan["label"]} — {plan["meses"]} meses{badge}</td>'
            f'<td class="precio-final">{total_uf_mes:.1f} UF/mes</td>'
            f'<td>{(total_uf_mes * plan["meses"]):.1f} UF</td>'
            f'</tr>'
        )
        filas.append(fila)

    html = ''
    html += (
        '<p>La suite de servicios puede contratarse bajo distintos plazos de permanencia, '
        'segun las necesidades de planificacion y presupuesto de la organizacion. '
        'Recomendamos el Plan Anual para programas de ciberseguridad continuos, '
        'asegurando cobertura y continuidad operativa durante todo el periodo.</p>'
    )
    html += (
        '<table class="tabla-planes">'
        '<tr>'
        '<th>Plan / Plazo</th>'
        '<th>Valor mensual</th>'
        '<th>Total del periodo</th>'
        '</tr>'
    )
    html += "".join(filas)
    html += "</table>"
    html += (
        '<div class="nota-pie">Valores netos, no incluyen IVA. Facturacion mensual durante '
        'la vigencia del plan contratado.</div>'
    )
    return _page_banner("Planes de Contratación", html)


def sec_condiciones(data: dict) -> str:
    condiciones = data.get("conditions", [])
    if not any(linea.strip() for linea in condiciones):
        return ""
    html = ''
    for linea in condiciones:
        if linea.strip():
            html += f'<div class="condicion-linea">{linea}</div>'
        else:
            html += "<br>"
    return _page_banner("Condiciones Comerciales", html)


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORIZACIÓN
# ══════════════════════════════════════════════════════════════════════════════

_CATEGORIAS = [
    "🛡  Detección y Respuesta",
    "🔑  Gestión de Identidades y Accesos",
    "☁  Protección de Infraestructura",
    "⚖  Cumplimiento y Gobernanza",
    "🎓  Capacitación y Desarrollo Seguro",
]

_KEYWORDS = {
    "🛡  Detección y Respuesta": [
        "incident","response","soc","monitoreo","vulnerability","pentest",
        "penetration","forensi","threat","detección","deteccion","respuesta",
        "brecha","intrusion","siem","edr","xdr","alerta","hunting","phishing",
        "ransomware","tabletop","nist","cis","controls","remediacion","remediación",
    ],
    "🔑  Gestión de Identidades y Accesos": [
        "iam","identidad","identity","acceso","access","mfa","autenticacion",
        "privileged","pam","zero trust","parche","patch","contraseña","password",
        "directorio","ldap","sso",
    ],
    "☁  Protección de Infraestructura": [
        "cloud","nube","aws","azure","gcp","firewall","red","network","endpoint",
        "backup","recuperacion","drp","infraestructura","servidor","server",
        "segmentacion","vpn","m365","entra","switch","wireless","telefon",
    ],
    "⚖  Cumplimiento y Gobernanza": [
        "cumplimiento","compliance","iso","normativa","ley","gdpr","gobernanza",
        "governance","audit","auditoria","legal","regulatorio","certificacion",
        "política","riesgo","risk","gap","sgsi","dpo","privacidad",
    ],
    "🎓  Capacitación y Desarrollo Seguro": [
        "capacitacion","training","awareness","simulacion","devsecops","desarrollo",
        "sast","dast","reporte","dashboard","kpi","concientizacion","taller",
    ],
}

def _cat_keywords(nombre, descripcion=""):
    if isinstance(descripcion, dict):
        descripcion = descripcion.get("intro", "") or ""
    texto = ((nombre or "") + " " + (descripcion or "")).lower()
    scores = {c: sum(1 for kw in kws if kw in texto) for c, kws in _KEYWORDS.items()}
    scores = {c: sum(1 for kw in kws if kw in texto) for c, kws in _KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else _CATEGORIAS[0]

def categorizar_servicios(servicios, usar_ia=True):
    mapeo = None
    if usar_ia:
        try:
            lista = "\n".join(f'- "{s["nombre"]}": {s.get("descripcion","")}' for s in servicios)
            cats  = "\n".join(f"  {i+1}. {c}" for i, c in enumerate(_CATEGORIAS))
            lista = "\n".join(f'- "{s["nombre"]}": {s.get("descripcion","")}' for s in servicios)
            cats  = "\n".join(f"  {i+1}. {c}" for i, c in enumerate(_CATEGORIAS))
            prompt = (f"Clasifica cada servicio en UNA categoría:\n{cats}\n\n"
                      f"Servicios:\n{lista}\n\n"
                       "Responde SOLO JSON sin backticks: {{nombre: categoría con emoji}}")
            "Responde SOLO JSON sin backticks: {{nombre: categoría con emoji}}"
            from app.services.ollama_service import MODEL as _OLLAMA_MODEL
            r = _requests.post(
                "http://localhost:11434/api/generate",
                json={"model": _OLLAMA_MODEL, "prompt": prompt,
                      "stream": False, "options": {"temperature": 0.1}},
                timeout=60)
            raw = r.json().get("response", "").replace("```json","").replace("```","").strip()
            mapeo = {n: (c if c in _CATEGORIAS else _cat_keywords(n))
                     for n, c in json.loads(raw).items()}
        except Exception:
            mapeo = None

    if mapeo is None:
        mapeo = {s["nombre"]: _cat_keywords(s["nombre"], s.get("descripcion",""))
                 for s in servicios}

    agrupado = {c: [] for c in _CATEGORIAS}
    for srv in servicios:
        cat = mapeo.get(srv["nombre"], _cat_keywords(srv["nombre"], srv.get("descripcion","")))
        cat = mapeo.get(srv["nombre"], _cat_keywords(srv["nombre"], srv.get("descripcion","")))
        agrupado[cat].append(srv)
    return {c: srvs for c, srvs in agrupado.items() if srvs}


# ══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

def generar_propuesta(data: dict, output_path: str, usar_ia: bool = True):
    from weasyprint import HTML, CSS

    company = data.get("company", {})

    portada_empresa = company.get("portada")
    interior_empresa = company.get("interior")

    # Solo exigir las imágenes base si NO hay imágenes configuradas
    if not portada_empresa and not BASE_PORTADA.exists():
        raise FileNotFoundError(
            f"No se encontró base_portada.png en {ASSETS_DIR}"
        )

    if not interior_empresa and not BASE_INTERIOR.exists():
        raise FileNotFoundError(
            f"No se encontró base_interior.png en {ASSETS_DIR}"
        )

    servicios_raw = data.get("servicios", [])

    # ── Enriquecer descripciones con IA estructurada ──────────────────────
    # Para cada servicio que tenga descripción de texto plano (no dict),
    # llamamos a Ollama para generar un JSON estructurado con viñetas.
    # Si Ollama falla, el servicio mantiene su descripción original.
    if usar_ia:
        empresa   = data.get("cliente_nombre", "la empresa")
        industria = data.get("industria", "tecnología")
        try:
            from app.services.ollama_service import generar_descripcion_servicio
            servicios_enriquecidos = []
            total = len(servicios_raw)
            for i, srv in enumerate(servicios_raw):
                desc = srv.get("descripcion", "")
                # Solo enriquecer si la descripción es texto plano y tiene contenido
                if isinstance(desc, str) and len(desc.strip()) > 20:
                    print(f"  [IA desc {i+1}/{total}] Estructurando: {srv.get('nombre', '')[:50]}...")
                    desc_estructurada = generar_descripcion_servicio(
                        nombre=srv.get("nombre", ""),
                        descripcion_base=desc,
                        empresa=empresa,
                        industria=industria
                    )
                    if desc_estructurada:
                        srv = dict(srv)
                        srv["descripcion"] = desc_estructurada
                servicios_enriquecidos.append(srv)
            servicios_raw = servicios_enriquecidos
        except Exception as e:
            print(f"  ⚠️  Enriquecimiento de descripciones falló: {e}. Usando texto plano.")

    agrupado = categorizar_servicios(servicios_raw, usar_ia=usar_ia)
    print("COMPANY RECIBIDA:")
    print(data.get("company"))
    css_str  = _css_base(data.get("company"))

    costos_html, total_uf_mes = sec_costos(agrupado, data)

    pages_html = [
        sec_portada(data),
        sec_introduccion(data),
        sec_alcance(data),
        sec_servicios(data, agrupado),
        sec_cumplimiento(data),
        sec_matriz(data),
        sec_metodologia(data),
        costos_html,
        sec_planes(total_uf_mes, data),
        sec_condiciones(data),
    ]

    full_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>{css_str}</style>
</head>
<body>
{"".join(pages_html)}
</body>
</html>"""

    from weasyprint import HTML, CSS
    print("CSS LENGTH:", len(css_str))

    HTML(string=full_html).write_pdf(
        output_path,
        stylesheets=[
            CSS(string=css_str)
        ]
    )

    print(f"✅ PDF generado: {output_path}")
