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
FRAME_H     = PAGE_H - 245 - 239  # ≈ 357 (entre bloque contenido superior e inferior)

# ── Frame portada ─────────────────────────────────────────────────────────
PORT_X  = 59.5           # alineado con logo CP y texto
PORT_Y  = 180            # por encima del logo CP
PORT_W  = 410            # hasta aprox x=470 (bloque blanco termina en 476)
PORT_H  = PAGE_H - PORT_Y - 200


# ══════════════════════════════════════════════════════════════════════════════
# CANVAS BACKGROUNDS — dibujados ANTES que el contenido del frame
# ══════════════════════════════════════════════════════════════════════════════

def _portada_bg(c, doc):
    """Dibuja el fondo completo de la portada."""
    c.saveState()

    # 1. Fondo azul completo
    c.setFillColor(AZUL)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # 2. Bloque blanco principal (área de texto)
    #    pdfplumber: x0=-24.3, x1=476.1, y0=118.9, y1=864.7
    #    RL (y desde abajo): y_bottom = PAGE_H - 864.7 = -22.8  → va debajo del borde, ok
    c.setFillColor(BLANCO)
    c.rect(-24.3, PAGE_H - 864.7, 500.4, 745.8, fill=1, stroke=0)

    # 3. Texto lateral vertical "CYBER-PROTECTION.CL"
    #    Posición aproximada: x≈530, centro vertical≈442
    c.setFillColor(VERDE)
    c.setFont(F_BOLD, 11)
    c.saveState()
    c.translate(565, PAGE_H / 2 + 20)
    c.rotate(90)
    txt = "C  Y  B  E  R  -  P  R  O  T  E  C  T  I  O  N  .  C  L"
    c.drawCentredString(0, 0, txt)
    c.restoreState()

    # 4. Círculo verde menta esquina inferior derecha
    #    Curva visible (pdfplumber): x0=275.4, x1=624.0, y0=514.2, y1=862.7
    #    cx=449.7, cy_RL (desde abajo)= PAGE_H - 688.5 = 153.8, radio=174.2
    cx, cy_rl, radio = 449.7, 153.8, 174.2
    c.setFillColor(VERDE)
    c.circle(cx, cy_rl, radio, fill=1, stroke=0)

    # 5. "Elaborado para:" — justo sobre el área del logo cliente
    #    Logo cliente: y_rl_top = 710.6 + 109.5 = 820 → texto a y≈ 155 (sobre círculo)
    c.setFillColor(AZUL)
    c.setFont(F_BOLD, 9)
    # Posición: centrado en el círculo, justo encima del logo
    c.drawCentredString(cx, cy_rl + radio/2 + 10, "Elaborado para:")

    # 6. Logo del CLIENTE — dentro del círculo
    #    pdfplumber: x0=416.9, x1=546.7, y0=22.2, y1=131.7
    #    RL: x=416.9, y_bottom = PAGE_H - 131.7 = 710.6, w=129.8, h=109.5
    logo_cliente = getattr(doc, '_logo_cliente', None)
    if logo_cliente and os.path.exists(logo_cliente):
        try:
            c.drawImage(logo_cliente,
                        cx - 64.9, cy_rl - 55,    # centrado en el círculo
                        width=129.8, height=109.5,
                        preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    # 7. Logo Cyber-Protection — inferior izquierda
    #    pdfplumber: x0=59.5, x1=278.6, y0=742, y1=823
    #    RL: x=59.5, y_bottom = PAGE_H - 823 = 19.3, w=219.1, h=81
    if os.path.exists(LOGO_CP):
        try:
            c.drawImage(LOGO_CP, 59.5, 19.3,
                        width=219.1, height=81.0,
                        preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    c.restoreState()


def _interior_bg(c, doc):
    """Dibuja el fondo de páginas interiores (2-N)."""
    c.saveState()

    # 1. Fondo verde menta completo
    c.setFillColor(VERDE)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # 2. Foto lateral izquierda — ancho real 91pts (recortamos la imagen)
    #    pdfplumber: x0=-20.1, x1=275.7 → imagen muy ancha, la recortamos a 91pts
    if os.path.exists(FOTO_EDIF):
        try:
            c.drawImage(FOTO_EDIF, 0, 0,
                        width=91, height=PAGE_H,
                        preserveAspectRatio=False, mask='auto')
        except Exception:
            # Fallback: rectángulo azul oscuro
            c.setFillColor(colors.HexColor("#1a3a6e"))
            c.rect(0, 0, 91, PAGE_H, fill=1, stroke=0)
    else:
        c.setFillColor(colors.HexColor("#1a3a6e"))
        c.rect(0, 0, 91, PAGE_H, fill=1, stroke=0)

    # 3. Bloque blanco contenido principal
    #    pdfplumber: x0=91.1, x1=566.8, y0=0.1, y1=603.3
    #    RL: x=91.1, y_bottom = PAGE_H - 603.3 = 238.9, w=475.7, h=603.3
    c.setFillColor(BLANCO)
    c.rect(91.1, PAGE_H - 603.3, 475.7, 603.3, fill=1, stroke=0)

    # 4. Bloque blanco logo superior derecho
    #    pdfplumber: x0=275.4, x1=595.7, y0=654.6, y1=842.3
    #    RL: x=275.4, y_bottom=0, w=320.3, h=187.7
    c.rect(275.4, PAGE_H - 842.3, 320.3, 187.7, fill=1, stroke=0)

    # 5. Logo Cyber-Protection — superior derecha
    #    pdfplumber: x0=301.6, x1=569.4, y0=699.5, y1=797.8
    #    RL: x=301.6, y_bottom = PAGE_H - 797.8 = 44.1, w=267.8, h=98.3
    if os.path.exists(LOGO_CP):
        try:
            # Centramos el logo en el bloque blanco con márgenes razonables
            logo_w, logo_h = 220, 75
            logo_x = 301.6 + (267.8 - logo_w) / 2
            logo_y = PAGE_H - 797.8 + (98.3 - logo_h) / 2
            c.drawImage(LOGO_CP, logo_x, logo_y,
                        width=logo_w, height=logo_h,
                        preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

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
            fontName=F_BOLD, fontSize=34, textColor=AZUL,
            leading=42, spaceAfter=12),
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
        sp(160),   # Espaciado superior (debajo del área de logo CP que está en x=59 y=19)
        Paragraph(titulo, st["titulo_portada"]),
        sp(16),
        Paragraph("Preparado para:", st["sub_portada"]),
        Paragraph(data.get("preparado_para", ""), st["sub_portada"]),
        sp(10),
        Paragraph(data.get("objetivo", ""), st["obj_portada"]),
        PageBreak(),
    ]


def sec_introduccion(data, st):
    elems = [NextPageTemplate('Interior'), sp(30)]
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
    elems = [sp(30)]

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
    story = [sp(30)]
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
    elems = [sp(30)]
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
    elems = [sp(30)]
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
    elems = [sp(30)]
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
    elems = [sp(30)]
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
    frame_portada = Frame(
        x1=59.5,
        y1=120,                        # sobre el logo CP (y_bottom=19.3 + h=81 ≈ 100)
        width=390,                     # ancho cómodo dentro del bloque blanco
        height=PAGE_H - 120 - 130,    # desde y=120 hasta y=PAGE_H-130
        leftPadding=0, rightPadding=0,
        topPadding=0, bottomPadding=0,
        id='portada',
    )

    # INTERIOR: frame dentro del bloque blanco de contenido
    # Bloque blanco: x=91.1, y_bottom=239, h=603.3 → y_top = 842.3
    # El contenido real empieza aprox a y_plumber=261 → RL y = 841.89-261 = 580
    # Frame: desde x=124 (margen interno) hasta x=566, y desde 245 hasta 603
    ancho_interior = 566.8 - 124      # ≈ 442.8 pts
    frame_interior = Frame(
        x1=124,
        y1=245,                        # sobre el borde inferior del bloque blanco
        width=ancho_interior,
        height=PAGE_H - 245 - 239,    # ≈ 358 pts dentro del bloque blanco
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
    if logo_cliente and os.path.exists(logo_cliente):
        try:
            tmp = "/tmp/_logo_cliente_portada.png"
            img = PILImage.open(logo_cliente)
            # Convertir a RGBA para preservar transparencia si existe
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
