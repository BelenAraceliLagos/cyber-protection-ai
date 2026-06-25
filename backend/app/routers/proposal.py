"""
Router de Propuestas — genera PDFs de preventa usando IA local (Ollama).
Ollama es OBLIGATORIO. Sin IA no se genera ningún documento.

Endpoint principal:
  POST /proposals/generate
"""

import os
import uuid
import base64
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.client import Client
from app.models.service import Service
from app.models.company import Company

from app.services.ollama_service import generar_textos_completos
from app.services.generate_proposal import generar_propuesta

router = APIRouter(
    prefix="/proposals",
    tags=["Proposals"]
)

# ─── Schemas ──────────────────────────────────────────────────────────

class ProposalRequest(BaseModel):
    cliente_id: int
    service_ids: List[int]
    titulo_proyecto: Optional[str] = None
    antecedente: Optional[str] = ""
    logo_cliente_path: Optional[str] = None
    logo_base64: Optional[str] = None   # imagen base64 del logo del cliente
    company_id: Optional[int] = None

class ProposalResponse(BaseModel):
    mensaje: str
    archivo: str


# ─── Construcción del dict de datos para el generador PDF ─────────────

def construir_data_propuesta(
    cliente,
    servicios,
    textos,
    titulo_proyecto,
    logo_cliente_path=None,
    company=None
) -> dict:

    servicios_pdf = []
    for s in servicios:
        servicios_pdf.append({
            "nombre": s.name,
            "descripcion": s.description or "",
            "base_price": s.base_price,
        })

    # Matriz de valor por servicio
    beneficios_map = {
        "incident":      ("Continuidad Operativa",        "Respuesta inmediata ante incidentes críticos."),
        "response":      ("Continuidad Operativa",        "Contención y erradicación de amenazas activas."),
        "asesor":        ("Reducción de Vulnerabilidades", "Fortalece la postura de seguridad estratégica."),
        "cumplimiento":  ("Mitigación de Riesgos Legales", "Evita multas y sanciones regulatorias."),
        "pentest":       ("Detección Proactiva",           "Identifica vulnerabilidades antes que los atacantes."),
        "monitoreo":     ("Visibilidad Continua",          "Alertas en tiempo real ante amenazas emergentes."),
        "mdr":           ("Detección Avanzada",            "Cobertura 24/7 con inteligencia artificial."),
        "forense":       ("Preservación de Evidencia",     "Análisis forense para respuesta legal y técnica."),
        "endpoint":      ("Protección de Dispositivos",    "Prevención en cada punto final de la organización."),
        "identidad":     ("Control de Accesos",            "Elimina cuentas comprometidas y accesos residuales."),
        "vulnerabilidad":("Remediación Proactiva",         "Cierra brechas antes de que sean explotadas."),
        "phishing":      ("Cultura de Seguridad",          "Reduce el factor humano como vector de ataque."),
        "tabletop":      ("Preparación Organizacional",    "Valida protocolos de respuesta bajo condiciones reales."),
        "cloud":         ("Seguridad en la Nube",          "Configuración segura de entornos cloud críticos."),
        "inteligencia":  ("Anticipación de Amenazas",      "Información táctica sobre actores y vectores activos."),
    }

    matriz_pdf = []
    
    for s in servicios:
        nombre_lower = s.name.lower()
        beneficio = "Protección Integral"
        valor = "Mejora la resiliencia organizacional."

        for kw, (b, v) in beneficios_map.items():
            if kw in nombre_lower:
                beneficio, valor = b, v
                break
        matriz_pdf.append({
            "servicio":       s.name,
            "beneficio":      beneficio,
            "valor_agregado": valor,
        })

    return {
        "titulo_proyecto":   titulo_proyecto,
        "preparado_para":    f"{cliente.contact_name} — {cliente.company_name}",
        "industria":         cliente.industry or "tecnología",
        "objetivo": (
            f"Fortalecer la postura de ciberseguridad de {cliente.company_name} "
            f"mediante servicios especializados, cumplimiento normativo y "
            f"respuesta efectiva ante amenazas."
        ),
        "logo_cliente": logo_cliente_path,
        
        "company": {
            "name": company.name if company else "",

            "logo": company.logo_path if company else None,

            "portada": company.portada_path if company else None,

            "interior": company.interior_path if company else None,

            "primary_color": company.primary_color if company else None,

            "secondary_color": company.secondary_color if company else None,
            
            "portada_config": company.portada_config if company else None
        },

        # Textos generados por IA
        "introduccion":             textos["introduccion"],
        "frase_clave":              textos["frase_clave"],
        "alcance_intro":            textos["alcance_intro"],
        "valor_estrategico":        textos["valor_estrategico"],
        "cierre_intro":             textos["cierre_intro"],

        "antecedente_titulo":       textos.get("antecedente_titulo"),
        "antecedente_descripcion":  textos.get("antecedente_descripcion", ""),
        "antecedente_bullets":      textos.get("antecedente_bullets", []),
        
        "subtitulo_servicios": f"Servicios Seleccionados para {cliente.company_name}",
        "servicios":           servicios_pdf,

        "cumplimiento": {
            "intro": "Alineación con el marco legal chileno y estándares internacionales.",
            "bullets": [
                "Ley 21.459 (Delitos Informáticos): Cumplimiento de protocolos de preservación de evidencia.",
                "Ley 19.628 (Protección de la Vida Privada): Gestión segura de datos sensibles.",
                "Alineación ISO 27001: Implementación de controles bajo estándares globales.",
            ],
        },
        "matriz_valor": matriz_pdf,

        "metodologia": [
            "Diagnóstico Inicial: Evaluación del estado actual de seguridad de la organización.",
            "Plan de Mitigación: Priorización y ejecución de controles según nivel de riesgo.",
            "Monitoreo y Reporte: Entrega de informes ejecutivos periódicos sobre el estado de seguridad.",
        ],
        "diferenciadores": [
            f"Conocimiento de {cliente.industry or 'la industria del cliente'}: Soluciones adaptadas al contexto real.",
            "Alineación con el CSIRT Nacional: Coordinación con organismos de ciberseguridad de Chile.",
        ],

        "nota_costos": (
            "Valores referenciales. Costos definitivos a confirmar tras reunión de alcance."
        ),

        "conditions": [
            "Los valores son netos y no incluyen IVA.",
            "Los costos de despacho fuera de la Región Metropolitana son por cuenta del cliente.",
            "",
            "Formas de pago: Contado, Transferencia Electrónica.",
            "",
            "Modalidad Proyecto (implementaciones, evaluaciones, pentesting, tabletop):",
            "50% al inicio de los trabajos.",
            "50% a la entrega de la implementación funcional.",
            "",
            "Modalidad Consultoría / Servicios Recurrentes (MDR, monitoreo, IR retainer, etc.):",
            "Facturación mensual, pago a 30 días desde la emisión de la factura (mes vencido).",
            "",
            "Servicio Técnico Gamer Chile SPA.  |  R.U.T.: 76.771.397-5",
            "La Capitanía 80, oficina 108, Las Condes, Santiago – Chile.",
            "Tel.: +56 9 4951 2772",
            "",
            "Transferencias Electrónicas — Banco Estado",
            "Chequera Electrónica Empresa N° 20470014891",
        ],
    }


# ─── ENDPOINT PRINCIPAL ────────────────────────────────────────────────

@router.post("/generate")
def generate_proposal(
    request: ProposalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Genera una propuesta PDF con IA local (Ollama). Obligatorio.
    Si Ollama no está disponible retorna error 503.
    """

    # 1. Validar cliente
    cliente = db.query(Client).filter(Client.id == request.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    # 1.5 Validar compañía emisora
    if not request.company_id:
        raise HTTPException(status_code=400, detail="Debe seleccionar una empresa emisora")

    company = db.query(Company).filter(Company.id == request.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    if not company.active:
        raise HTTPException(status_code=400, detail="Company is inactive")

    # 2. Validar servicios
    servicios = db.query(Service).filter(
        Service.id.in_(request.service_ids)
    ).all()
    if not servicios:
        raise HTTPException(status_code=404, detail="No se encontraron los servicios indicados")

    # 3. Título del proyecto
    titulo = request.titulo_proyecto or "Propuesta de Servicios de Ciberseguridad"

    # 4. Generar textos con IA — SIN fallback genérico
    try:
        textos = generar_textos_completos(
            empresa_cliente=cliente.company_name,
            empresa_emisora=company.name,
            industria=cliente.industry or "tecnología",
            servicios=[s.name for s in servicios],
            antecedente=request.antecedente or "",
            contacto=cliente.contact_name or ""
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Ollama no disponible: {str(e)}. Inicia Ollama con 'ollama serve' antes de generar."
        )

    # 5. Resolver logo — se pasa el data URI directamente (más robusto que archivo temp)
    logo_uri = None
    if request.logo_base64:
        # El frontend ya envía un data URI completo: "data:image/...;base64,..."
        logo_uri = request.logo_base64
        print(f"   Logo recibido: {logo_uri[:50]}...")
    elif request.logo_cliente_path:
        # Fallback: path local (no usado normalmente)
        logo_uri = request.logo_cliente_path

    # 6. Construir el dict de datos
    data = construir_data_propuesta(
        cliente=cliente,
        servicios=servicios,
        textos=textos,
        titulo_proyecto=titulo,
        logo_cliente_path=logo_uri,
        company=company
    )

    # 7. Generar el PDF
    nombre_archivo = f"propuesta_{cliente.company_name.replace(' ', '_')}_{uuid.uuid4().hex[:8]}.pdf"
    output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "propuestas_generadas")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, nombre_archivo)

    import traceback

    try:
       generar_propuesta(data, output_path)

    except Exception as e:
        traceback.print_exc()

        print("ERROR PDF:", str(e))

        raise HTTPException(
            status_code=500,
            detail=f"Error generando PDF: {str(e)}"
        )

    # 8. Devolver el PDF como descarga
    return FileResponse(
        path=output_path,
        media_type="application/pdf",
        filename=nombre_archivo,
        headers={"Content-Disposition": f"attachment; filename={nombre_archivo}"}
    )


@router.get("/preview/{cliente_id}")
def preview_proposal_data(
    cliente_id: int,
    service_ids: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Devuelve en JSON los datos del cliente y servicios sin crear el PDF."""
    cliente = db.query(Client).filter(Client.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    ids = [int(i) for i in service_ids.split(",") if i.strip().isdigit()]
    servicios = db.query(Service).filter(Service.id.in_(ids)).all()

    return {
        "cliente": {
            "id":        cliente.id,
            "empresa":   cliente.company_name,
            "contacto":  cliente.contact_name,
            "email":     cliente.email,
            "id":        cliente.id,
            "industria": cliente.industry,
        },
        "servicios": [
            {"id": s.id, "nombre": s.name, "precio_uf": s.base_price}
            for s in servicios
        ],
        "total_uf": sum(s.base_price for s in servicios),
        "mensaje": "Datos listos. Usa POST /proposals/generate para crear el PDF."
    }