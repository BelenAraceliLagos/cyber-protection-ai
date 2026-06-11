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
import requests as _requests
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


def _css_base() -> str:
    portada_uri  = _img_b64(BASE_PORTADA)  if BASE_PORTADA.exists()  else ""
    interior_uri = _img_b64(BASE_INTERIOR) if BASE_INTERIOR.exists() else ""
    return f"""
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
    color: {AZUL};
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
    width: 148mm;
}}

/* Portada título: Segoe UI Bold, 38.5pt */
.portada-titulo {{
    font-family:   'Segoe UI', 'Segoe UI Variable', Arial, sans-serif;
    font-size:     38.5pt;
    font-weight:   700;
    color:         {AZUL};
    line-height:   1.12;
    margin-bottom: 12mm;
}}
/* "Preparado para:" y=336.5pt → 118.8mm desde arriba
   Distancia desde top del content: 336.5-118.3=218.2pt = 77mm */
/* Portada etiquetas: Segoe UI Bold */
.portada-prep-label {{
    font-family:   'Segoe UI', 'Segoe UI Variable', Arial, sans-serif;
    font-size:     12pt;
    font-weight:   700;
    color:         {AZUL};
    margin-top:    77mm;
    margin-bottom: 2mm;
}}
.portada-cliente-nombre {{
    font-family:   'Segoe UI', 'Segoe UI Variable', Arial, sans-serif;
    font-size:     14pt;
    font-weight:   700;
    color:         {AZUL};
    margin-bottom: 8mm;
    line-height:   1.3;
}}
.portada-objetivo {{
    font-family:   'Segoe UI', 'Segoe UI Variable', Arial, sans-serif;
    font-size:     12pt;
    font-weight:   700;
    color:         {AZUL};
    line-height:   1.4;
}}
/* Logo cliente — centrado en círculo verde menta
   Centro círculo: x=163.4mm, y=250.4mm, radio≈56mm */
.portada-elaborado {{
    position:        absolute;
    left:            123mm;
    top:             228mm;
    width:           80mm;
    font-family:     'Segoe UI', 'Segoe UI Variable', Arial, sans-serif;
    font-size:       10pt;
    font-weight:     700;
    color:           {AZUL};
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
    font-family:   'Segoe UI', 'Segoe UI Variable', Arial, sans-serif;
    background:    {VERDE};
    color:         {AZUL};
    font-size:     26pt;
    font-weight:   700;
    padding:       3mm 8mm;
    display:       block;
    width:         160mm;
    line-height:   1.1;
    position:      absolute;
    left:          32mm;
    top:           45mm;
}}
.banner-titulo.banner-alcance-pos {{
    top: 45mm;
}}
.banner-titulo.banner-costos-pos {{
    top: 64mm;
}}

/* Body independiente del banner — posicionado exactamente donde empieza el texto real */
.banner-body-alcance {{
    position: absolute;
    left:     38mm;
    top:      119mm;
    width:    152mm;
}}
.banner-body-costos {{
    position: absolute;
    left:     38mm;
    top:      91mm;
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
    color:         {AZUL};
    margin-bottom: 3mm;
    line-height:   1.15;
}}

/* H2 — Subtítulos de sección (Valor Estratégico, etc.)
   Fuente: Segoe UI Bold, 14pt */
h2 {{
    font-family:   'Segoe UI', 'Segoe UI Variable', Arial, sans-serif;
    font-size:     14pt;
    font-weight:   700;
    color:         {AZUL};
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
    color:         {AZUL};
    margin-top:    3mm;
    margin-bottom: 1.5mm;
}}

.hr {{
    border:         none;
    border-top:     0.8pt solid {AZUL};
    margin-bottom:  3mm;
    margin-top:     0.5mm;
}}

/* Body — párrafos de cuerpo general
   Fuente: Segoe UI Regular, 10.5pt, justificado */
p {{
    font-family:   'Segoe UI', 'Segoe UI Variable', Arial, sans-serif;
    font-size:     10.5pt;
    font-weight:   400;
    color:         {AZUL};
    line-height:   1.55;
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
    color:         {AZUL};
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
    color:         {AZUL};
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
    color:         {AZUL};
    line-height:   1.5;
}}
/* Cargo firma: Segoe UI Regular */
.firma-cargo {{
    font-family:   'Segoe UI', 'Segoe UI Variable', Arial, sans-serif;
    font-size:     10.5pt;
    font-weight:   400;
    color:         {AZUL};
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
}}
.srv-lista li {{
    font-family:   'Segoe UI', 'Segoe UI Variable', Arial, sans-serif;
    font-size:     10pt;
    font-weight:   400;
    color:         {AZUL};
    line-height:   1.5;
    margin-bottom: 1.5mm;
    text-align:    justify;
}}
.srv-lista li strong {{
    font-weight: 700;
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
    background:    {AZUL};
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
    color:         {AZUL};
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
    background:  {AZUL};
    color:       white;
    font-weight: bold;
    font-size:   10pt;
    padding:     3mm;
}}
.tabla-costos tr.total-row td.right {{ text-align: center; }}

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
    background:    {AZUL};
    color:         white;
    padding:       2mm 2.5mm;
    text-align:    left;
    font-weight:   700;
    border:        0.5pt solid #CCCCCC;
}}
.tabla-matriz td {{
    font-family:   'Segoe UI', 'Segoe UI Variable', Arial, sans-serif;
    font-weight:   400;
    color:         {AZUL};
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
    color:         {AZUL};
    line-height:   1.7;
}}
/* Nota pie: Segoe UI Italic */
.nota-pie {{
    font-family:   'Segoe UI', 'Segoe UI Variable', Arial, sans-serif;
    font-size:     8.5pt;
    font-weight:   400;
    font-style:    italic;
    color:         {AZUL};
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
    titulo  = data.get("titulo_portada_servicios") or data.get("titulo_proyecto", "")
    para    = data.get("preparado_para", "")
    obj     = data.get("objetivo", "")
    # Logo del cliente — zona inferior derecha de la portada
    logo_src = _img_uri(data.get("logo_cliente") or "")
    logo_html = (
        f'<div class="portada-elaborado">'
        f'<div style="font-size:9pt;font-weight:700;color:#155FCF;letter-spacing:0.5pt;">Elaborado para:</div>'
        f'<img src="{logo_src}" style="max-width:60mm;max-height:34mm;object-fit:contain;">'
        f'</div>'
    ) if logo_src else ''
    return f'''
<div class="page-portada">
  <div class="portada-content">
    <div class="portada-titulo">{titulo}</div>
    <div class="portada-prep-label">Preparado para:</div>
    <div class="portada-cliente-nombre">{para}</div>
    <div class="portada-objetivo">{obj}</div>
  </div>
  {logo_html}
</div>'''


def sec_introduccion(data: dict) -> str:
    html = f'''
<h1>Introducción</h1>
<div class="hr"></div>
<p>{data.get("introduccion", "")}</p>
<p class="cita">"{data.get("frase_clave", "")}"</p>
<p>{data.get("cierre_intro", "")}</p>
<div class="firma-bloque">
  <div class="firma-cargo">________________________</div>
  <div class="firma-nombre">Andrés Barrientos Cisternas</div>
  <div class="firma-cargo">CTO / CYBERPROTECTION.CL</div>
</div>'''
    return _page_std(html)


def sec_alcance(data: dict) -> str:
    html = '<h1>Alcance</h1><div class="hr"></div>'
    html += f'<p>{data.get("alcance_intro", "")}</p>'
    if data.get("antecedente_titulo"):
        html += f'<h3>{data["antecedente_titulo"]}</h3>'
        for par in (data.get("antecedente_descripcion") or "").split("\n\n"):
            if par.strip():
                html += f"<p>{par.strip()}</p>"
    for b in (data.get("antecedente_bullets") or []):
        html += f"<ul><li>{b}</li></ul>"
    return _page_std(html)


def _srv_item(srv: dict) -> str:
    """Genera un <li> compacto para un servicio."""
    nombre = srv.get("nombre", "")
    desc = ""
    if srv.get("descripcion"):
        desc = srv["descripcion"].split("|")[0].strip()
    elif srv.get("bullets"):
        b0 = srv["bullets"][0] if srv["bullets"] else ""
        desc = b0.replace("Descripción: ", "").strip()
    # Sin truncado — descripción completa para mejor presentación
    # (el diseño de lista compacta maneja el espacio adecuadamente)
    if desc:
        return f'<li><strong>{nombre}:</strong> {desc}</li>'
    return f'<li><strong>{nombre}</strong></li>'


def sec_servicios(data: dict, agrupado: dict) -> str:
    """
    Divide servicios en páginas de máx 8 items para evitar overflow.
    Cada página tiene su propio div.page-interior.
    """
    MAX_POR_PAGINA = 8
    total = sum(len(v) for v in agrupado.values())

    # Construir lista plana de bloques: cada bloque es (titulo_cat, [items_html])
    bloques = []
    encabezado = (
        '<h1>Servicios Propuestos:</h1>'
        '<div class="hr"></div>'
        f'<p>Suite de {total} servicio{"s" if total != 1 else ""} especializados '
        f'en {len(agrupado)} área{"s" if len(agrupado) != 1 else ""} de cobertura, '
        f'diseñados para proteger integralmente su organización.</p>'
    )

    paginas = []
    pagina_actual = encabezado
    items_en_pagina = 0

    for cat, srvs in agrupado.items():
        # Añadir header de categoría
        cat_html = f'<h2>{cat}</h2><ul class="srv-lista">'
        items_cat = [_srv_item(s) for s in srvs]

        # Si añadir esta categoría completa desborda la página, paginar
        for i, item in enumerate(items_cat):
            if items_en_pagina >= MAX_POR_PAGINA:
                # Cerrar lista si estaba abierta y guardar página
                pagina_actual += '</ul>'
                paginas.append(_page_std(pagina_actual))
                pagina_actual = f'<h2>{cat} </h2><ul class="srv-lista">'
                items_en_pagina = 0
            elif i == 0:
                pagina_actual += cat_html
            pagina_actual += item
            items_en_pagina += 1

    # Cerrar última lista y agregar valor estratégico
    pagina_actual += '</ul>'
    if data.get("valor_estrategico"):
        pagina_actual += f'<h2>Valor Estratégico</h2><p>{data["valor_estrategico"]}</p>'
    paginas.append(_page_std(pagina_actual))

    return "".join(paginas)


def sec_cumplimiento(data: dict) -> str:
    """Página propia: Cumplimiento Normativo."""
    cum = data.get("cumplimiento", {})
    html = '<h1>Cumplimiento Normativo</h1><div class="hr"></div>'
    html += f'<p><strong>{cum.get("intro", "")}</strong></p><ul>'
    for b in cum.get("bullets", []):
        html += f"<li>{b}</li>"
    html += "</ul>"
    return _page_std(html)


def sec_matriz(data: dict) -> str:
    """Matriz de Valor — paginada en bloques de MAX_MATRIZ filas."""
    MAX_FILAS = 10
    filas = data.get("matriz_valor", [])
    if not filas:
        return _page_std('<h1>Matriz de Valor</h1><div class="hr"></div>')

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
        titulo = '<h1>Matriz de Valor</h1><div class="hr"></div><p><strong>Áreas que cubre el servicio y aporta a la organización</strong></p>' if es_primera else '<h1>Matriz de Valor </h1><div class="hr"></div>'
        tabla = TH
        for f in chunk:
            tabla += f'''<tr>
              <td>{f.get("servicio","")}</td>
              <td>{f.get("beneficio","")}</td>
              <td>{f.get("valor_agregado","")}</td>
            </tr>'''
        tabla += "</table>"
        paginas.append(_page_std(titulo + tabla))

    return "".join(paginas)


def sec_metodologia(data: dict) -> str:
    html = '<h2>4. Metodología de Trabajo</h2><div class="hr"></div><ul>'
    for b in data.get("metodologia", []):
        html += f"<li>{b}</li>"
    html += "</ul>"
    html += '<h2>5. Diferenciadores Locales</h2><div class="hr"></div><ul>'
    for b in data.get("diferenciadores", []):
        html += f"<li>{b}</li>"
    html += "</ul>"
    return _page_std(html)


def sec_costos(agrupado: dict, data: dict) -> str:
    """Centro de Costos — paginado en bloques de 14 filas (cat+srv)."""
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
        paginas.append(_page_std(titulo + tabla))

    return "".join(paginas)


def sec_condiciones(data: dict) -> str:
    html = '<h1>Condiciones Comerciales:</h1><div class="hr"></div>'
    for linea in data.get("condiciones", []):
        if linea.strip():
            html += f'<div class="condicion-linea">{linea}</div>'
        else:
            html += "<br>"
    return _page_std(html)


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
    texto = ((nombre or "") + " " + (descripcion or "")).lower()
    scores = {c: sum(1 for kw in kws if kw in texto) for c, kws in _KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else _CATEGORIAS[0]

def categorizar_servicios(servicios, usar_ia=True):
    mapeo = None
    if usar_ia:
        try:
            lista = "\n".join(f'- "{s["nombre"]}": {s.get("descripcion","")}' for s in servicios)
            cats  = "\n".join(f"  {i+1}. {c}" for i, c in enumerate(_CATEGORIAS))
            prompt = (f"Clasifica cada servicio en UNA categoría:\n{cats}\n\n"
                      f"Servicios:\n{lista}\n\n"
                      "Responde SOLO JSON sin backticks: {{nombre: categoría con emoji}}")
            r = _requests.post(
                "http://localhost:11434/api/generate",
                json={"model": "gemma3:4b", "prompt": prompt,
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
        agrupado[cat].append(srv)
    return {c: srvs for c, srvs in agrupado.items() if srvs}


# ══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

def generar_propuesta(data: dict, output_path: str, usar_ia: bool = True):
    from weasyprint import HTML, CSS

    if not BASE_PORTADA.exists():
        raise FileNotFoundError(
            f"No se encontró base_portada.png en {ASSETS_DIR}. "
            "Copia base_portada.png y base_interior.png a la carpeta assets/.")
    if not BASE_INTERIOR.exists():
        raise FileNotFoundError(
            f"No se encontró base_interior.png en {ASSETS_DIR}.")

    servicios_raw = data.get("servicios", [])
    agrupado = categorizar_servicios(servicios_raw, usar_ia=usar_ia)
    css_str  = _css_base()

    pages_html = [
        sec_portada(data),
        sec_introduccion(data),
        sec_alcance(data),
        sec_servicios(data, agrupado),
        sec_cumplimiento(data),
        sec_matriz(data),
        sec_metodologia(data),
        sec_costos(agrupado, data),
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

    HTML(string=full_html).write_pdf(output_path)
    print(f"✅ PDF generado: {output_path}")
