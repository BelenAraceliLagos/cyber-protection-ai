"""
Router de Propuestas — genera PDFs de preventa usando IA local (Ollama).

Endpoint principal:
  POST /proposals/generate

Recibe cliente_id + lista de service_ids seleccionados,
llama a Ollama para generar los textos,
y devuelve un PDF listo para descargar.
"""

import os
import uuid
import tempfile
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

# Importamos los módulos del generador
from app.services.ollama_service import generar_textos_completos
from app.services.generate_proposal import generar_propuesta

router = APIRouter(
    prefix="/proposals",
    tags=["Proposals"]
)

# ─── Schemas de entrada ────────────────────────────────────────────────

class ProposalRequest(BaseModel):
    cliente_id: int
    service_ids: List[int]
    titulo_proyecto: Optional[str] = None
    antecedente: Optional[str] = ""
    logo_cliente_path: Optional[str] = None   # ruta local al logo del cliente
    usar_ia: Optional[bool] = True            # False = textos genéricos sin Ollama

class ProposalResponse(BaseModel):
    mensaje: str
    archivo: str


# ─── Textos genéricos (fallback sin IA) ───────────────────────────────

def textos_genericos(cliente: Client, servicios: List[Service]) -> dict:
    nombres = [s.name for s in servicios]
    nombres_str = ", ".join(nombres)
    return {
        "introduccion": (
            f"Cyber-Protection presenta a {cliente.company_name} una propuesta integral "
            f"de servicios de ciberseguridad diseñada para proteger sus activos críticos. "
            f"Nuestra experiencia en {nombres_str} nos permite ofrecer soluciones adaptadas "
            f"a las necesidades específicas de su organización, garantizando la continuidad "
            f"operativa y el cumplimiento normativo."
        ),
        "frase_clave": (
            f"Queremos brindarle tranquilidad y seguridad a {cliente.company_name}. "
            f"Nuestro enfoque combina tecnología de vanguardia con experiencia local "
            f"para construir una defensa robusta y sostenible."
        ),
        "alcance_intro": (
            f"La propuesta para {cliente.company_name} abarca los servicios de {nombres_str}, "
            f"estableciendo un ecosistema de resiliencia basado en tres pilares: "
            f"Respuesta, Asesoría Estratégica y Cumplimiento Normativo."
        ),
        "valor_estrategico": (
            f"Invertir en ciberseguridad no es un costo, es una ventaja competitiva. "
            f"Para {cliente.company_name}, nuestra propuesta representa la diferencia "
            f"entre la exposición al riesgo y la continuidad operativa garantizada."
        ),
        "cierre_intro": (
            "Al hacerlo, fortalecemos la confianza en su organización "
            "y aseguramos la continuidad de sus operaciones."
        ),
    }


# ─── Construcción del dict de datos para el generador PDF ─────────────

def construir_data_propuesta(
    cliente: Client,
    servicios: List[Service],
    textos: dict,
    titulo_proyecto: str,
    logo_cliente_path: Optional[str]
) -> dict:

    nombres_servicios = [s.name for s in servicios]

    # Servicios formateados para el PDF
    servicios_pdf = []
    for s in servicios:
        servicios_pdf.append({
            "nombre": s.name,
            "bullets": [
                f"Descripción: {s.description}" if s.description
                else "Servicio especializado en ciberseguridad corporativa.",
                f"Valor mensual referencial: {s.base_price:.0f} UF.",
            ]
        })

    # Costos para la tabla
    costos_pdf = []
    for s in servicios:
        costos_pdf.append({
            "servicio": s.name,
            "costo": f"{s.base_price:.1f} UF"
        })

    # Matriz de valor genérica por servicio
    matriz_pdf = []
    beneficios_map = {
        "Incident Response": ("Continuidad Operativa", "Respuesta inmediata ante incidentes."),
        "Asesoría": ("Reducción de Vulnerabilidades", "Fortalece la postura de seguridad."),
        "Cumplimiento": ("Mitigación de Riesgos Legales", "Evita multas y sanciones."),
        "Pentesting": ("Detección Proactiva", "Identifica vulnerabilidades antes que los atacantes."),
        "Monitoreo": ("Visibilidad Continua", "Alertas en tiempo real ante amenazas."),
    }
    for s in servicios:
        beneficio, valor = "Protección Integral", "Mejora la resiliencia organizacional."
        for key, (b, v) in beneficios_map.items():
            if key.lower() in s.name.lower():
                beneficio, valor = b, v
                break
        matriz_pdf.append({
            "servicio": s.name,
            "beneficio": beneficio,
            "valor_agregado": valor,
        })

    return {
        "titulo_proyecto": titulo_proyecto,
        "preparado_para": f"{cliente.contact_name} — {cliente.company_name}",
        "objetivo": (
            f"Fortalecer la ciberseguridad de {cliente.company_name} "
            f"mediante soluciones especializadas y cumplimiento normativo."
        ),
        "logo_cliente": logo_cliente_path,

        # Textos generados por IA (o genéricos)
        "introduccion":     textos["introduccion"],
        "frase_clave":      textos["frase_clave"],
        "alcance_intro":    textos["alcance_intro"],
        "valor_estrategico": textos["valor_estrategico"],
        "cierre_intro":     textos["cierre_intro"],

        "antecedente_titulo": None,
        "antecedente_descripcion": "",
        "antecedente_bullets": [],

        "subtitulo_servicios": f"Servicios Seleccionados para {cliente.company_name}",
        "servicios": servicios_pdf,

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
            f"Conocimiento de la industria {cliente.industry or 'del cliente'}: Soluciones adaptadas al contexto real.",
            "Alineación con el CSIRT Nacional: Coordinación con organismos de ciberseguridad de Chile.",
        ],

        "costos": costos_pdf,
        "nota_costos": (
            "Valores referenciales. Costos definitivos a confirmar tras reunión de alcance."
        ),

        "condiciones": [
            "Los valores son netos y no incluyen IVA.",
            "Los costos de despacho fuera de la Región Metropolitana son por cuenta del cliente.",
            "",
            "Formas de pago: Contado, Transferencia Electrónica.",
            "",
            "Hitos de Facturación:",
            "80% al inicio de los trabajos.",
            "20% a la entrega de la implementación funcional.",
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
    Genera una propuesta PDF personalizada para un cliente.

    - Consulta el cliente y los servicios seleccionados en la BD
    - Opcionalmente usa Ollama/Gemma para generar los textos
    - Devuelve el PDF como descarga directa
    """

    # 1. Validar cliente
    cliente = db.query(Client).filter(Client.id == request.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    # 2. Validar servicios
    servicios = db.query(Service).filter(
        Service.id.in_(request.service_ids)
    ).all()
    if not servicios:
        raise HTTPException(status_code=404, detail="No se encontraron los servicios indicados")

    # 3. Título del proyecto
    titulo = request.titulo_proyecto or f"Propuesta {cliente.company_name}"

    # 4. Generar textos (IA o genéricos)
    if request.usar_ia:
        try:
            textos = generar_textos_completos(
                empresa_cliente=cliente.company_name,
                industria=cliente.industry or "tecnología",
                servicios=[s.name for s in servicios],
                antecedente=request.antecedente or ""
            )
        except RuntimeError as e:
            # Si Ollama no está disponible, usar textos genéricos
            print(f"⚠️  Ollama no disponible: {e}. Usando textos genéricos.")
            textos = textos_genericos(cliente, servicios)
    else:
        textos = textos_genericos(cliente, servicios)

    # 5. Construir el dict de datos
    data = construir_data_propuesta(
        cliente=cliente,
        servicios=servicios,
        textos=textos,
        titulo_proyecto=titulo,
        logo_cliente_path=request.logo_cliente_path
    )

    # 6. Generar el PDF en carpeta temporal
    nombre_archivo = f"propuesta_{cliente.company_name.replace(' ', '_')}_{uuid.uuid4().hex[:8]}.pdf"
    output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "propuestas_generadas")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, nombre_archivo)

    try:
        generar_propuesta(data, output_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando PDF: {str(e)}")

    # 7. Devolver el PDF como descarga
    return FileResponse(
        path=output_path,
        media_type="application/pdf",
        filename=nombre_archivo,
        headers={"Content-Disposition": f"attachment; filename={nombre_archivo}"}
    )


@router.get("/preview/{cliente_id}")
def preview_proposal_data(
    cliente_id: int,
    service_ids: str,   # "1,2,3" separado por comas
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Devuelve en JSON los datos que se usarían para generar la propuesta,
    sin crear el PDF. Útil para previsualizar antes de generar.
    """
    cliente = db.query(Client).filter(Client.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    ids = [int(i) for i in service_ids.split(",") if i.strip().isdigit()]
    servicios = db.query(Service).filter(Service.id.in_(ids)).all()

    return {
        "cliente": {
            "id": cliente.id,
            "empresa": cliente.company_name,
            "contacto": cliente.contact_name,
            "email": cliente.email,
            "industria": cliente.industry,
        },
        "servicios": [
            {"id": s.id, "nombre": s.name, "precio_uf": s.base_price}
            for s in servicios
        ],
        "total_uf": sum(s.base_price for s in servicios),
        "mensaje": "Datos listos. Usa POST /proposals/generate para crear el PDF."
    }
