"""
generate_proposal.py — Generador PDF fiel al diseño corporativo Cyber-Protection.
Reescrito con coordenadas pixel-perfect extraídas del PDF base UNAB con pdfplumber.

PORTADA (pág. 1):
  - Fondo azul #155FCF completo
  - Rect blanco: x=-24.3, y_bottom=-22.4, w=500.4, h=745.8
  - Círculo verde menta: cx=449.7, cy_rl=153.8, radio=174.2
  - Texto lateral vertical "CYBER-PROTECTION.CL": x=530, centro y=442
  - Logo CP: x=59.5, y_rl=19.3, w=219.1, h=81
  - Logo cliente: x=416.9, y_rl=710.6, w=129.8, h=109.5
  - "Elaborado para:" texto sobre logo cliente

INTERIORES (págs. 2-8):
  - Fondo verde menta #8EE3C8
  - Foto lateral: x=0, y=0, w=91, h=842.3
  - Bloque blanco contenido: x=91.1, y_rl=239.0, w=475.7, h=603.3
  - Bloque blanco logo sup-der: x=275.4, y_rl=0, w=320.3, h=187.7
  - Logo CP: x=301.6, y_rl=44.5, w=267.8, h=98.3
"""

import os, json, math
import requests as _requests
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame,
    Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether, NextPageTemplate, Flowable
)
from PIL import Image as PILImage

# ── Fuentes estándar PDF (siempre disponibles) ─────────────────────────────
F_REG  = 'Helvetica'
F_BOLD = 'Helvetica-Bold'
F_IT   = 'Helvetica-Oblique'

# ── Colores exactos del PDF base ───────────────────────────────────────────
AZUL   = colors.HexColor("#155FCF")   # fondo portada + texto azul
VERDE  = colors.HexColor("#8EE3C8")   # fondo páginas interiores
BLANCO = colors.white
GRIS   = colors.HexColor("#333333")

# ── Dimensiones de página A4 ───────────────────────────────────────────────
PAGE_W, PAGE_H = A4                    # 595.28 x 841.89

# ── Rutas assets ───────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.normpath(os.path.join(BASE_DIR, '..', '..', 'assets'))
LOGO_CP    = os.path.join(ASSETS_DIR, 'logo_cyberprotection.png')
FOTO_EDIF  = os.path.join(ASSETS_DIR, 'foto_edificio.jpg')

# ── Frame interior: desde x=124 (texto empieza ahí en original) ───────────
FRAME_X     = 124        # margen izquierdo del texto en páginas interiores
FRAME_W     = 566.8 - FRAME_X   # ≈ 442.8 pts
FRAME_Y     = 245        # margen inferior (sobre el bloque logo)
FRAME_H     = PAGE_H - 245 - 260  # ≈ 357 (entre bloque contenido superior e inferior)

# ── Frame portada ─────────────────────────────────────────────────────────
PORT_X  = 59.5           # alineado con logo CP y texto
PORT_Y  = 180            # por encima del logo CP
PORT_W  = 410            # hasta aprox x=470 (bloque blanco termina en 476)
PORT_H  = PAGE_H - PORT_Y - 200


# ══════════════════════════════════════════════════════════════════════════════
# CANVAS BACKGROUNDS — dibujados ANTES que el contenido del frame
# ══════════════════════════════════════════════════════════════════════════════

def _portada_bg(c, doc):
    """Dibuja el fondo completo de la portada — coordenadas pixel-perfect del base UNAB."""
    c.saveState()

    # 1. Fondo azul completo
    c.setFillColor(AZUL)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # 2. Bloque blanco principal
    # Toca borde SUPERIOR, borde INFERIOR y borde IZQUIERDO
    # x=-24.33 (sale por izquierda), y_bottom=-22.46 (sale por abajo)
    # y_top = PAGE_H (toca borde superior)
    # h = PAGE_H - (-22.46) = PAGE_H + 22.46 = 864.71
    c.setFillColor(BLANCO)
    c.rect(-12, 150, 500.44, PAGE_H + 22.46, fill=1, stroke=0)

    # 3. Texto lateral -90° (de abajo hacia arriba = igual al PDF base)
    # BASE: chars en x=520.5, desde top=51 a top=350, matrix=[0,-0.75,0.75,0,...]
    # Rotación -90° con centro en x=526.858, centrado verticalmente
    c.setFillColor(VERDE)
    c.setFont(F_BOLD, 15)
    c.saveState()
    c.translate(526.858, (PAGE_H / 2) + 150)
    c.rotate(-90)
    c.drawCentredString(0, 0, "C  Y  B  E  R  -  P  R  O  T  E  C  T  I  O  N  .  C  L")
    c.restoreState()

    # 4. Círculo verde menta — esquina inferior-derecha
    # BASE: cx_plumb=449.71, cy_plumb=688.45 → cy_rl=153.80, radio=174.28
    # Sale 28.48pts por la DERECHA y 20.47pts por ABAJO → solo visible cuadrante sup-izq
    c.setFillColor(VERDE)
    c.circle(700, -12, 400, fill=1, stroke=0)

    # 5. "Elaborado para:" centrado en la parte visible del círculo
    # Área visible: x de 275.43 a 595.50, y_rl de 0 a ~328
    vis_cx = (275.43 + 595.50) / 2   # = 435.47
    vis_cy = 164.0
    c.setFillColor(GRIS)
    c.setFont(F_BOLD, 9)
    c.drawCentredString(vis_cx, vis_cy + 30, "Elaborado para:")

    # 6. Logo del CLIENTE — dentro del círculo visible
    logo_cliente = getattr(doc, '_logo_cliente', None)
    if logo_cliente and os.path.exists(logo_cliente):
        try:
            c.drawImage(logo_cliente,
                        vis_cx - 64.9, vis_cy - 54.75,
                        width=129.8, height=109.5,
                        preserveAspectRatio=True, mask='auto')
        except Exception:
            # Fallback: nombre del cliente en texto
            c.setFont(F_BOLD, 13)
            c.drawCentredString(vis_cx, vis_cy, doc._nombre_cliente or "")
    else:
        # Sin logo: mostrar nombre cliente
        nombre = getattr(doc, '_nombre_cliente', '')
        if nombre:
            c.setFont(F_BOLD, 13)
            c.drawCentredString(vis_cx, vis_cy, nombre)

    # 7. Logo Cyber-Protection — borde inferior izquierdo
    # BASE: x0=59.55, y0_plumb=742.01, y1_plumb=823.04 → y_rl_bottom=PAGE_H-823.04=19.21
    # w=219.08, h=81.03
    if os.path.exists(LOGO_CP):
        try:
            c.drawImage(LOGO_CP, 59.55, PAGE_H - 100,
                        width=219.08, height=81.03,
                        preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    c.restoreState()


def _interior_bg(c, doc):
    """
    Fondo páginas interiores (pág 2 en adelante). SIN círculo.

    Estructura:
    - Fondo verde menta completo
    - Foto lateral: x=-20.08, w=295.79, altura completa
    - Bloque blanco contenido: toca borde SUPERIOR, termina en y_bottom=238.95
    - Bloque blanco logo: esquina SUPERIOR DERECHA (x0=275.42, toca borde superior)
    - Logo CP: dentro del bloque blanco superior derecho, pegado arriba
    - Texto lateral -90°
    """
    c.saveState()

    # 1. Fondo verde menta completo
    c.setFillColor(VERDE)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # 2. Foto lateral — coordenadas exactas del base
    # x0=-20.08, y0=-18.40, w=295.79, h=860.86
    if os.path.exists(FOTO_EDIF):
        try:
            c.drawImage(FOTO_EDIF, -20.08, -18.40,
                        width=295.79, height=860.86,
                        preserveAspectRatio=False, mask='auto')
        except Exception:
            c.setFillColor(colors.HexColor("#1a3a6e"))
            c.rect(-20.08, 0, 295.79, PAGE_H, fill=1, stroke=0)
    else:
        c.setFillColor(colors.HexColor("#1a3a6e"))
        c.rect(-20.08, 0, 295.79, PAGE_H, fill=1, stroke=0)

    # 3. Bloque blanco contenido
    # Toca borde SUPERIOR (y_top=PAGE_H), NO toca borde inferior
    # RL: x=91.12, y_bottom=PAGE_H-603.30=238.95, h=603.23
    c.setFillColor(BLANCO)
    c.rect(91.12, PAGE_H - 603.30, 475.68, 603.23, fill=1, stroke=0)

    # 4. Bloque blanco logo — esquina SUPERIOR DERECHA
    # x0=275.42, toca borde superior: y_top=PAGE_H, h=187.64
    bloque_logo_h = 187.64
    c.rect(275.42, PAGE_H - bloque_logo_h, 320.31, bloque_logo_h, fill=1, stroke=0)

    # 5. Logo CP — pegado al borde superior derecho
    # w=267.85, h=98.29, margen 20pts desde borde superior
    if os.path.exists(LOGO_CP):
        try:
            logo_y = PAGE_H - 98.29 - 20
            c.drawImage(LOGO_CP, 301.55, logo_y,
                        width=267.85, height=98.29,
                        preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    # 6. Texto lateral -90° en franja verde derecha
    c.setFillColor(AZUL)
    c.setFont(F_BOLD, 12)
    c.saveState()
    c.translate(584, PAGE_H / 2+80)
    c.rotate(-90)
    c.drawCentredString(0, 0, "C  Y  B  E  R  -  P  R  O  T  E  C  T  I  O  N  .  C  L")
    c.restoreState()

    c.restoreState()

def _on_page(c, doc):
    if doc.page == 1:
        _portada_bg(c, doc)
    else:
        _interior_bg(c, doc)


# ══════════════════════════════════════════════════════════════════════════════
# ESTILOS
# ══════════════════════════════════════════════════════════════════════════════

def get_styles():
    return {
        # — Portada —
        "titulo_portada": ParagraphStyle("titulo_portada",
            fontName=F_BOLD, fontSize=38.5, textColor=AZUL,
            leading=46, spaceAfter=10),
        "sub_portada": ParagraphStyle("sub_portada",
            fontName=F_BOLD, fontSize=12, textColor=AZUL,
            leading=16, spaceAfter=4),
        "obj_portada": ParagraphStyle("obj_portada",
            fontName=F_BOLD, fontSize=12, textColor=AZUL,
            leading=16, spaceAfter=6),

        # — Encabezados interiores —
        "h1": ParagraphStyle("h1",
            fontName=F_BOLD, fontSize=26, textColor=AZUL,
            leading=32, spaceAfter=6, spaceBefore=0),
        "h2": ParagraphStyle("h2",
            fontName=F_BOLD, fontSize=16, textColor=AZUL,
            leading=22, spaceAfter=5, spaceBefore=8),
        "h3": ParagraphStyle("h3",
            fontName=F_BOLD, fontSize=13, textColor=AZUL,
            leading=17, spaceAfter=4, spaceBefore=6),

        # — Cuerpo —
        "body": ParagraphStyle("body",
            fontName=F_REG, fontSize=11, textColor=AZUL,
            leading=16, spaceAfter=7, alignment=TA_JUSTIFY),
        "body_bold": ParagraphStyle("body_bold",
            fontName=F_BOLD, fontSize=11, textColor=AZUL,
            leading=16, spaceAfter=5, alignment=TA_JUSTIFY),
        "cita": ParagraphStyle("cita",
            fontName=F_BOLD, fontSize=11, textColor=AZUL,
            leading=16, spaceAfter=7, alignment=TA_JUSTIFY),
        "bullet": ParagraphStyle("bullet",
            fontName=F_REG, fontSize=11, textColor=AZUL,
            leading=16, spaceAfter=4, leftIndent=14, alignment=TA_JUSTIFY),
        "subtitulo": ParagraphStyle("subtitulo",
            fontName=F_REG, fontSize=11, textColor=AZUL,
            leading=16, spaceAfter=8, alignment=TA_JUSTIFY),

        # — Firma —
        "firma": ParagraphStyle("firma",
            fontName=F_REG, fontSize=10, textColor=AZUL,
            leading=14, alignment=TA_CENTER),
        "firma_bold": ParagraphStyle("firma_bold",
            fontName=F_BOLD, fontSize=10, textColor=AZUL,
            leading=14, alignment=TA_CENTER),

        # — Tabla servicios —
        "cat_header": ParagraphStyle("cat_header",
            fontName=F_BOLD, fontSize=12, textColor=BLANCO, leading=16),
        "srv_nombre": ParagraphStyle("srv_nombre",
            fontName=F_BOLD, fontSize=10, textColor=AZUL, leading=13, spaceAfter=2),
        "srv_desc": ParagraphStyle("srv_desc",
            fontName=F_REG, fontSize=9, textColor=GRIS, leading=12),

        # — Tabla costos y matriz —
        "th": ParagraphStyle("th",
            fontName=F_BOLD, fontSize=11, textColor=BLANCO),
        "td": ParagraphStyle("td",
            fontName=F_REG, fontSize=10, textColor=AZUL, leading=14),
        "td_bold": ParagraphStyle("td_bold",
            fontName=F_BOLD, fontSize=10, textColor=AZUL, leading=14),

        # — Condiciones —
        "cond": ParagraphStyle("cond",
            fontName=F_REG, fontSize=11, textColor=AZUL,
            leading=17, spaceAfter=3),
        "nota": ParagraphStyle("nota",
            fontName=F_IT, fontSize=9, textColor=AZUL, alignment=TA_CENTER),
    }


# ── Helpers ────────────────────────────────────────────────────────────────

def sp(h=8):
    return Spacer(1, h)

def hr(color=AZUL, grosor=0.8):
    return HRFlowable(width="100%", thickness=grosor,
                      color=color, spaceAfter=6, spaceBefore=2)

def bullet_item(texto, st):
    return Paragraph(f"• {texto}", st["bullet"])


# ══════════════════════════════════════════════════════════════════════════════
# SECCIONES
# ══════════════════════════════════════════════════════════════════════════════

def sec_portada(data, st):
    """
    Portada: el texto flota en el bloque blanco.
    Logo CP e ícono cliente se dibujan en el canvas (_portada_bg).
    El frame empieza en y=180 para dejar espacio al logo CP abajo.
    """
    titulo = data.get("titulo_portada_servicios") or data.get("titulo_proyecto", "")

    return [
        sp(5),     # El frame ya posiciona el texto en la zona correcta
        Paragraph(titulo, st["titulo_portada"]),
        sp(19),
        Paragraph("Preparado para:", st["sub_portada"]),
        Paragraph(data.get("preparado_para", ""), st["sub_portada"]),
        sp(13),
        Paragraph(data.get("objetivo", ""), st["obj_portada"]),
        PageBreak(),
    ]


def sec_introduccion(data, st):
    elems = [NextPageTemplate('Interior'), sp(2)]
    elems += [
        Paragraph("Introducción", st["h1"]),
        hr(),
        sp(5),
        Paragraph(data.get("introduccion", ""), st["body"]),
        sp(8),
        Paragraph(f'"{data.get("frase_clave", "")}"', st["cita"]),
        sp(6),
        Paragraph(data.get("cierre_intro", ""), st["body"]),
        sp(20),
        Paragraph("________________________", st["firma"]),
        sp(3),
        Paragraph("Andrés Barrientos Cisternas", st["firma_bold"]),
        Paragraph("CTO / CYBERPROTECTION.CL", st["firma"]),
        PageBreak(),
    ]
    return elems


def sec_alcance(data, st, ancho):
    """Alcance con header de caja tipo banner azul + contenido."""
    elems = [sp(2)]

    # Banner "Alcance" — como en el original: caja azul con texto blanco
    hdr = Table([[Paragraph("Alcance", st["cat_header"])]],
                colWidths=[ancho])
    hdr.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), AZUL),
        ("TOPPADDING",    (0,0),(-1,-1), 10),
        ("BOTTOMPADDING", (0,0),(-1,-1), 10),
        ("LEFTPADDING",   (0,0),(-1,-1), 12),
    ]))
    elems += [hdr, sp(12)]
    elems.append(Paragraph(data.get("alcance_intro", ""), st["body"]))
    elems.append(sp(8))

    if data.get("antecedente_titulo"):
        elems.append(Paragraph(data["antecedente_titulo"], st["h3"]))
        for par in (data.get("antecedente_descripcion") or "").split("\n\n"):
            if par.strip():
                elems.append(Paragraph(par.strip(), st["body"]))
    if data.get("antecedente_bullets"):
        for b in data["antecedente_bullets"]:
            elems.append(bullet_item(b, st))

    elems.append(PageBreak())
    return elems


def sec_servicios(data, st, agrupado, ancho):
    """Servicios agrupados por categoría en tabla de 2 columnas."""
    col_w = ancho / 2

    def _bloque_cat(nombre_cat, servicios):
        blk = []
        hdr = Table([[Paragraph(f"■  {nombre_cat}", st["cat_header"])]],
                    colWidths=[ancho])
        hdr.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), AZUL),
            ("TOPPADDING",    (0,0),(-1,-1), 7),
            ("BOTTOMPADDING", (0,0),(-1,-1), 7),
            ("LEFTPADDING",   (0,0),(-1,-1), 10),
        ]))
        blk.append(hdr)
        pares = [servicios[i:i+2] for i in range(0, len(servicios), 2)]
        for idx, par in enumerate(pares):
            celdas = []
            for srv in par:
                inner = [Paragraph(f"+ {srv['nombre']}", st["srv_nombre"])]
                if srv.get("descripcion"):
                    inner.append(Paragraph(
                        srv["descripcion"].split("|")[0][:100], st["srv_desc"]))
                celdas.append(inner)
            if len(par) == 1:
                celdas.append(Paragraph("", st["srv_desc"]))
            bg = colors.HexColor("#EBF3FF") if idx % 2 == 0 else BLANCO
            fila = Table([celdas], colWidths=[col_w, col_w])
            fila.setStyle(TableStyle([
                ("BACKGROUND",    (0,0),(-1,-1), bg),
                ("VALIGN",        (0,0),(-1,-1), "TOP"),
                ("TOPPADDING",    (0,0),(-1,-1), 8),
                ("BOTTOMPADDING", (0,0),(-1,-1), 8),
                ("LEFTPADDING",   (0,0),(-1,-1), 10),
                ("LINEAFTER",     (0,0),(0,-1), 0.5, colors.HexColor("#CCCCCC")),
            ]))
            blk.append(fila)
        blk.append(sp(8))
        return KeepTogether(blk) if len(servicios) <= 4 else blk

    total = sum(len(v) for v in agrupado.values())
    story = [sp(2)]
    story += [
        Paragraph("Servicios Propuestos:", st["h1"]),
        hr(),
        Paragraph(
            f"Suite de {total} servicio{'s' if total != 1 else ''} especializados "
            f"en {len(agrupado)} área{'s' if len(agrupado) != 1 else ''} de cobertura, "
            "diseñados para proteger integralmente su organización.",
            st["subtitulo"]),
    ]
    for cat, srvs in agrupado.items():
        blk = _bloque_cat(cat, srvs)
        if isinstance(blk, list):
            story.extend(blk)
        else:
            story.append(blk)

    if data.get("valor_estrategico"):
        story += [sp(6), Paragraph("Valor Estratégico", st["h2"]),
                  Paragraph(data["valor_estrategico"], st["body"])]
    story.append(PageBreak())
    return story


def sec_cumplimiento_matriz(data, st, ancho):
    elems = [sp(2)]
    if data.get("cumplimiento"):
        cum = data["cumplimiento"]
        elems += [
            Paragraph('C. Cumplimiento Normativo — "Gobernanza y Ley"', st["h2"]),
            Paragraph(cum.get("intro", ""), st["body_bold"]),
        ]
        for b in cum.get("bullets", []):
            elems.append(bullet_item(b, st))
        elems.append(sp(10))

    elems += [
        Paragraph("Matriz de Valor", st["h1"]),
        hr(),
        Paragraph("Áreas que cubre el servicio y aporta a la organización",
                  st["body_bold"]),
        sp(8),
    ]
    if data.get("matriz_valor"):
        W1, W2, W3 = ancho * 0.35, ancho * 0.33, ancho * 0.32
        tbl_data = [[
            Paragraph("<b>Servicio</b>",         st["td_bold"]),
            Paragraph("<b>Beneficio Directo</b>", st["td_bold"]),
            Paragraph("<b>Valor Agregado</b>",    st["td_bold"]),
        ]]
        for f in data["matriz_valor"]:
            tbl_data.append([
                Paragraph(f.get("servicio", ""),       st["td"]),
                Paragraph(f.get("beneficio", ""),      st["td"]),
                Paragraph(f.get("valor_agregado", ""), st["td"]),
            ])
        tbl = Table(tbl_data, colWidths=[W1, W2, W3], repeatRows=1)
        tbl.setStyle(TableStyle([
            ("BACKGROUND",     (0,0),(-1,0),  AZUL),
            ("TEXTCOLOR",      (0,0),(-1,0),  BLANCO),
            ("ROWBACKGROUNDS", (0,1),(-1,-1), [BLANCO, colors.HexColor("#EBF3FF")]),
            ("GRID",           (0,0),(-1,-1), 0.4, colors.HexColor("#CCCCCC")),
            ("VALIGN",         (0,0),(-1,-1), "TOP"),
            ("TOPPADDING",     (0,0),(-1,-1), 8),
            ("BOTTOMPADDING",  (0,0),(-1,-1), 8),
            ("LEFTPADDING",    (0,0),(-1,-1), 8),
        ]))
        elems.append(tbl)
    elems.append(PageBreak())
    return elems


def sec_metodologia(data, st):
    elems = [sp(2)]
    elems += [Paragraph("4. Metodología de Trabajo", st["h2"]), hr()]
    for b in data.get("metodologia", []):
        elems.append(bullet_item(b, st))
    elems += [sp(10), Paragraph("5. Diferenciadores Locales", st["h2"]), hr()]
    for b in data.get("diferenciadores", []):
        elems.append(bullet_item(b, st))
    elems.append(PageBreak())
    return elems


def sec_costos(agrupado, st, ancho, nota=""):
    C1, C2 = ancho * 0.65, ancho * 0.35
    total = 0.0
    elems = [sp(2)]
    elems += [
        Paragraph("Centro de Costos:", st["h1"]),
        hr(),
        Paragraph(
            "Valores referenciales por área. "
            "Costos definitivos a confirmar en reunión de alcance.",
            st["subtitulo"]),
    ]
    # Header tabla
    hdr = Table([[Paragraph("Servicio", st["th"]),
                  Paragraph("Costo Mensual (UF)", st["th"])]],
                colWidths=[C1, C2])
    hdr.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), AZUL),
        ("TOPPADDING",    (0,0),(-1,-1), 9),
        ("BOTTOMPADDING", (0,0),(-1,-1), 9),
        ("LEFTPADDING",   (0,0),(-1,-1), 10),
        ("ALIGN",         (1,0),(1,-1),  "CENTER"),
        ("LINEBELOW",     (0,0),(-1,-1), 2, VERDE),
    ]))
    elems.append(hdr)

    for cat, srvs in agrupado.items():
        cat_row = Table([[Paragraph(f"■  {cat}", st["td_bold"]),
                          Paragraph("", st["td"])]],
                        colWidths=[C1, C2])
        cat_row.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), colors.HexColor("#EBF3FF")),
            ("TOPPADDING",    (0,0),(-1,-1), 6),
            ("BOTTOMPADDING", (0,0),(-1,-1), 6),
            ("LEFTPADDING",   (0,0),(-1,-1), 10),
            ("LINEBELOW",     (0,0),(-1,-1), 0.8, VERDE),
        ]))
        elems.append(cat_row)
        for i, srv in enumerate(srvs):
            precio = srv.get("base_price", 0)
            total += precio if isinstance(precio, (int, float)) else 0
            precio_str = (f"{precio:.1f}" if isinstance(precio, (int, float)) and precio > 0
                          else "A convenir")
            bg = BLANCO if i % 2 == 0 else colors.HexColor("#F5F9FF")
            row = Table([[Paragraph(f"  {srv['nombre']}", st["td"]),
                          Paragraph(precio_str, st["td"])]],
                        colWidths=[C1, C2])
            row.setStyle(TableStyle([
                ("BACKGROUND",    (0,0),(-1,-1), bg),
                ("TOPPADDING",    (0,0),(-1,-1), 6),
                ("BOTTOMPADDING", (0,0),(-1,-1), 6),
                ("LEFTPADDING",   (0,0),(-1,-1), 10),
                ("ALIGN",         (1,0),(1,-1),  "CENTER"),
                ("LINEBELOW",     (0,0),(-1,-1), 0.3, colors.HexColor("#CCCCCC")),
            ]))
            elems.append(row)

    total_str = f"{total:.1f} UF/mes" if total > 0 else "A convenir"
    pie = Table([[Paragraph("TOTAL SUITE", st["th"]),
                  Paragraph(total_str, st["th"])]],
                colWidths=[C1, C2])
    pie.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), AZUL),
        ("TOPPADDING",    (0,0),(-1,-1), 10),
        ("BOTTOMPADDING", (0,0),(-1,-1), 10),
        ("LEFTPADDING",   (0,0),(-1,-1), 10),
        ("ALIGN",         (1,0),(1,-1),  "CENTER"),
        ("LINEABOVE",     (0,0),(-1,-1), 2, VERDE),
    ]))
    elems.append(pie)
    if nota:
        elems += [sp(8), Paragraph(nota, st["nota"])]
    elems.append(PageBreak())
    return elems


def sec_condiciones(data, st):
    elems = [sp(2)]
    elems += [Paragraph("Condiciones Comerciales:", st["h1"]), hr(), sp(5)]
    for linea in data.get("condiciones", []):
        if linea.strip():
            elems.append(Paragraph(linea, st["cond"]))
        else:
            elems.append(sp(5))
    return elems


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORIZACIÓN AUTOMÁTICA
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
    scores = {c: sum(1 for kw in kws if kw in texto)
              for c, kws in _KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else _CATEGORIAS[0]

def categorizar_servicios(servicios, usar_ia=True):
    mapeo = None
    if usar_ia:
        try:
            lista = "\n".join(
                f'- "{s["nombre"]}": {s.get("descripcion", "")}' for s in servicios)
            cats = "\n".join(f"  {i+1}. {c}" for i, c in enumerate(_CATEGORIAS))
            prompt = (f"Clasifica cada servicio en UNA categoría:\n{cats}\n\n"
                      f"Servicios:\n{lista}\n\n"
                      "Responde SOLO JSON sin backticks: {nombre: categoría con emoji}")
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
        cat = mapeo.get(srv["nombre"],
                        _cat_keywords(srv["nombre"], srv.get("descripcion","")))
        agrupado[cat].append(srv)
    return {c: srvs for c, srvs in agrupado.items() if srvs}


# ══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

def generar_propuesta(data: dict, output_path: str, usar_ia: bool = True):
    """
    Genera PDF de propuesta con diseño corporativo fiel al original.

    Args:
        data: dict con todos los campos de la propuesta
        output_path: ruta donde guardar el PDF
        usar_ia: si True, usa Ollama para categorizar servicios
    """
    servicios_raw = data.get("servicios", [])
    agrupado = categorizar_servicios(servicios_raw, usar_ia=usar_ia)
    st = get_styles()

    # ── Frames ────────────────────────────────────────────────────────────────
    # PORTADA: frame sobre el bloque blanco, desde x=59.5 (alineado con logo CP)
    # Espacio inferior reservado para logo CP (aprox 120pts desde abajo)
    # PORTADA: bloque blanco x0=-24.33, y_bottom=-22.46, y_top=723.32
    # Logo CP en y_rl = PAGE_H-823.04 = 19.21 a 19.21+81.03 = 100.24
    # Título debe aparecer en top=118 → y_rl = PAGE_H-118 = 724 (tope del frame)
    frame_portada = Frame(
        x1=59.55,                      # alineado con logo CP y texto del base
        y1=110,                        # sobre el logo CP (tope: 19.21+81.03=100.24)
        width=400,                     # hasta aprox x=460 (dentro del bloque blanco)
        height=PAGE_H - 110 - 88,     # desde y=110 hasta y≈724 (debajo del borde sup)
        leftPadding=0, rightPadding=0,
        topPadding=0, bottomPadding=0,
        id='portada',
    )

    # INTERIOR: frame dentro del bloque blanco de contenido
    # Molde pág 4 BASE: bloque blanco x0=91.12, y_bottom=238.95, h=603.23
    # Primer texto en x0=123.6, top=243.8 → y_rl=PAGE_H-243.8=598.45
    # Frame cubre desde y=245 (sobre borde inf del bloque) hasta y=835 (top del bloque)
    # height = 835 - 245 = 590 pts → texto fluye sin cortes entre páginas
    ancho_interior = 566.8 - 123.6    # = 443.2 pts
    frame_interior = Frame(
        x1=123.6,                      # x exacto del texto en pág 4 del base
        y1=245,                        # sobre el borde inferior del bloque blanco
        width=ancho_interior,
        height=590,                    # cubre zona completa del bloque blanco
        leftPadding=0, rightPadding=0,
        topPadding=0, bottomPadding=0,
        id='interior',
    )

    pt_portada  = PageTemplate(id='Portada',  frames=[frame_portada],  onPage=_portada_bg)
    pt_interior = PageTemplate(id='Interior', frames=[frame_interior], onPage=_interior_bg)

    doc = BaseDocTemplate(
        output_path,
        pagesize=A4,
        pageTemplates=[pt_portada, pt_interior],
        title=f"Propuesta — {data.get('titulo_proyecto', '')}",
        author="Cyber-Protection.cl",
    )

    # Pasar logo cliente al canvas mediante atributo del doc
    logo_cliente = data.get("logo_cliente")
    doc._nombre_cliente = data.get("nombre_cliente", data.get("preparado_para", ""))
    if logo_cliente and os.path.exists(logo_cliente):
        try:
            tmp = "/tmp/_logo_cliente_portada.png"
            img = PILImage.open(logo_cliente)
            img.save(tmp, format="PNG")
            doc._logo_cliente = tmp
        except Exception:
            doc._logo_cliente = None
    else:
        doc._logo_cliente = None

    # ── Story ─────────────────────────────────────────────────────────────────
    story = []
    story += sec_portada(data, st)
    story += sec_introduccion(data, st)
    story += sec_alcance(data, st, ancho_interior)
    story += sec_servicios(data, st, agrupado, ancho_interior)
    story += sec_cumplimiento_matriz(data, st, ancho_interior)
    story += sec_metodologia(data, st)
    story += sec_costos(agrupado, st, ancho_interior, data.get("nota_costos", ""))
    story += sec_condiciones(data, st)

    doc.build(story)
    print(f"✅ PDF generado: {output_path}")
