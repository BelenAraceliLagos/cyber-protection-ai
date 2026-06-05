"""
app/routers/opportunities.py
CRUD de Oportunidades de Venta, Hitos (Gantt) y Notas de actividad.
También expone el endpoint para generar el PDF directamente desde una oportunidad.
"""

import os
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.client import Client
from app.models.service import Service
from app.models.opportunity import Opportunity, Milestone, ActivityNote, EtapaVenta, TipoHito
from app.services.ollama_service import generar_textos_completos
from app.services.generate_proposal import generar_propuesta

router = APIRouter(prefix="/opportunities", tags=["Opportunities"])


# ══════════════════════════════════════════════════════════════════
# SCHEMAS
# ══════════════════════════════════════════════════════════════════

class MilestoneCreate(BaseModel):
    tipo: TipoHito
    titulo: str
    descripcion: Optional[str] = ""
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    completado: Optional[bool] = False

class MilestoneUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    completado: Optional[bool] = None

class MilestoneOut(BaseModel):
    id: int
    tipo: str
    titulo: str
    descripcion: Optional[str]
    fecha_inicio: Optional[datetime]
    fecha_fin: Optional[datetime]
    completado: bool
    class Config: from_attributes = True

class ActivityNoteCreate(BaseModel):
    contenido: str

class ActivityNoteOut(BaseModel):
    id: int
    contenido: str
    autor: Optional[str]
    creado_en: datetime
    class Config: from_attributes = True

class OpportunityCreate(BaseModel):
    cliente_id: int
    titulo: str
    etapa: Optional[EtapaVenta] = EtapaVenta.prospecto
    probabilidad: Optional[int] = 30
    valor_uf: Optional[float] = 0.0
    notas: Optional[str] = ""
    service_ids: Optional[List[int]] = []

class OpportunityUpdate(BaseModel):
    titulo: Optional[str] = None
    etapa: Optional[EtapaVenta] = None
    probabilidad: Optional[int] = None
    valor_uf: Optional[float] = None
    notas: Optional[str] = None
    service_ids: Optional[List[int]] = None

class OpportunityOut(BaseModel):
    id: int
    cliente_id: int
    cliente_nombre: Optional[str] = None
    titulo: str
    etapa: str
    probabilidad: int
    valor_uf: float
    notas: Optional[str]
    pdf_path: Optional[str]
    service_ids: List[int] = []
    hitos: List[MilestoneOut] = []
    notas_actividad: List[ActivityNoteOut] = []
    creado_en: Optional[datetime]
    actualizado_en: Optional[datetime]
    class Config: from_attributes = True

class GeneratePDFRequest(BaseModel):
    usar_ia: Optional[bool] = True
    antecedente: Optional[str] = ""
    logo_cliente_path: Optional[str] = None

# ══════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════

def _serialize(opp: Opportunity) -> dict:
    """Convierte el modelo ORM a dict limpio para la respuesta."""
    ids = []
    if opp.service_ids_str:
        ids = [int(x) for x in opp.service_ids_str.split(",") if x.strip().isdigit()]
    return {
        "id": opp.id,
        "cliente_id": opp.cliente_id,
        "cliente_nombre": opp.cliente.company_name if opp.cliente else None,
        "titulo": opp.titulo,
        "etapa": opp.etapa.value if hasattr(opp.etapa, "value") else opp.etapa,
        "probabilidad": opp.probabilidad,
        "valor_uf": opp.valor_uf,
        "notas": opp.notas,
        "pdf_path": opp.pdf_path,
        "service_ids": ids,
        "hitos": [
            {
                "id": h.id,
                "tipo": h.tipo.value if hasattr(h.tipo, "value") else h.tipo,
                "titulo": h.titulo,
                "descripcion": h.descripcion,
                "fecha_inicio": h.fecha_inicio.isoformat() if h.fecha_inicio else None,
                "fecha_fin": h.fecha_fin.isoformat() if h.fecha_fin else None,
                "completado": h.completado,
            }
            for h in opp.hitos
        ],
        "notas_actividad": [
            {
                "id": n.id,
                "contenido": n.contenido,
                "autor": n.autor,
                "creado_en": n.creado_en.isoformat() if n.creado_en else None,
            }
            for n in opp.notas_actividad
        ],
        "creado_en": opp.creado_en.isoformat() if opp.creado_en else None,
        "actualizado_en": opp.actualizado_en.isoformat() if opp.actualizado_en else None,
    }

def _textos_genericos(cliente: Client, servicios: list) -> dict:
    nombres = ", ".join(s.name for s in servicios)
    return {
        "introduccion": (
            f"Cyber-Protection presenta a {cliente.company_name} una propuesta integral "
            f"de ciberseguridad diseñada para proteger sus activos críticos a través de "
            f"{nombres}, garantizando continuidad operativa y cumplimiento normativo."
        ),
        "frase_clave": (
            f"Queremos brindarle tranquilidad y seguridad a {cliente.company_name}. "
            "Nuestro enfoque combina tecnología de vanguardia con experiencia local "
            "para construir una defensa robusta y sostenible."
        ),
        "alcance_intro": (
            f"La propuesta para {cliente.company_name} abarca los servicios de {nombres}, "
            "estableciendo un ecosistema de resiliencia basado en tres pilares: "
            "Respuesta, Asesoría Estratégica y Cumplimiento Normativo."
        ),
        "valor_estrategico": (
            f"Invertir en ciberseguridad es una ventaja competitiva. "
            f"Para {cliente.company_name}, esta propuesta representa la diferencia "
            "entre la exposición al riesgo y la continuidad operativa garantizada."
        ),
        "cierre_intro": (
            "Al hacerlo, fortalecemos la confianza en su organización "
            "y aseguramos la continuidad de sus operaciones."
        ),
    }


# ══════════════════════════════════════════════════════════════════
# OPORTUNIDADES — CRUD
# ══════════════════════════════════════════════════════════════════

@router.get("/")
def list_opportunities(
    etapa: Optional[str] = Query(None),
    cliente_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista todas las oportunidades, con filtros opcionales por etapa y cliente."""
    q = db.query(Opportunity)
    if etapa:
        q = q.filter(Opportunity.etapa == etapa)
    if cliente_id:
        q = q.filter(Opportunity.cliente_id == cliente_id)
    opps = q.order_by(Opportunity.actualizado_en.desc().nullslast()).all()
    return [_serialize(o) for o in opps]


@router.get("/pipeline")
def get_pipeline(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Devuelve las oportunidades agrupadas por etapa para el Kanban.
    También incluye métricas resumen para el Dashboard.
    """
    all_opps = db.query(Opportunity).all()
    etapas = ["prospecto", "propuesta", "negociacion", "aprobacion", "ganado", "perdido"]
    pipeline = {e: [] for e in etapas}
    for o in all_opps:
        etapa_key = o.etapa.value if hasattr(o.etapa, "value") else o.etapa
        if etapa_key in pipeline:
            pipeline[etapa_key].append(_serialize(o))

    activas = [o for o in all_opps
               if (o.etapa.value if hasattr(o.etapa,"value") else o.etapa)
               not in ("ganado", "perdido")]
    valor_total = sum(o.valor_uf for o in activas)
    prob_prom = (sum(o.probabilidad for o in activas) / len(activas)) if activas else 0

    return {
        "pipeline": pipeline,
        "metricas": {
            "total_activas": len(activas),
            "valor_pipeline_uf": round(valor_total, 1),
            "probabilidad_promedio": round(prob_prom),
            "total_ganadas": len(pipeline["ganado"]),
            "total_perdidas": len(pipeline["perdido"]),
        }
    }


@router.post("/", status_code=201)
def create_opportunity(
    body: OpportunityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cliente = db.query(Client).filter(Client.id == body.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    service_ids_str = ",".join(str(i) for i in (body.service_ids or []))
    opp = Opportunity(
        cliente_id=body.cliente_id,
        titulo=body.titulo,
        etapa=body.etapa,
        probabilidad=body.probabilidad,
        valor_uf=body.valor_uf,
        notas=body.notas,
        service_ids_str=service_ids_str,
        industria=cliente.industry,
    )
    db.add(opp)
    db.commit()
    db.refresh(opp)
    return _serialize(opp)


@router.get("/{opp_id}")
def get_opportunity(
    opp_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    return _serialize(opp)


@router.patch("/{opp_id}")
def update_opportunity(
    opp_id: int,
    body: OpportunityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")

    if body.titulo is not None:       opp.titulo = body.titulo
    if body.etapa is not None:        opp.etapa = body.etapa
    if body.probabilidad is not None: opp.probabilidad = body.probabilidad
    if body.valor_uf is not None:     opp.valor_uf = body.valor_uf
    if body.notas is not None:        opp.notas = body.notas
    if body.service_ids is not None:
        opp.service_ids_str = ",".join(str(i) for i in body.service_ids)

    opp.actualizado_en = datetime.utcnow()
    db.commit()
    db.refresh(opp)
    return _serialize(opp)


@router.delete("/{opp_id}", status_code=204)
def delete_opportunity(
    opp_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    db.delete(opp)
    db.commit()


# ══════════════════════════════════════════════════════════════════
# HITOS (GANTT)
# ══════════════════════════════════════════════════════════════════

@router.get("/{opp_id}/milestones")
def list_milestones(
    opp_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    return [
        {
            "id": h.id,
            "tipo": h.tipo.value if hasattr(h.tipo, "value") else h.tipo,
            "titulo": h.titulo,
            "descripcion": h.descripcion,
            "fecha_inicio": h.fecha_inicio.isoformat() if h.fecha_inicio else None,
            "fecha_fin": h.fecha_fin.isoformat() if h.fecha_fin else None,
            "completado": h.completado,
        }
        for h in opp.hitos
    ]


@router.post("/{opp_id}/milestones", status_code=201)
def create_milestone(
    opp_id: int,
    body: MilestoneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")

    hito = Milestone(
        opportunity_id=opp_id,
        tipo=body.tipo,
        titulo=body.titulo,
        descripcion=body.descripcion,
        fecha_inicio=body.fecha_inicio,
        fecha_fin=body.fecha_fin,
        completado=body.completado,
    )
    db.add(hito)
    db.commit()
    db.refresh(hito)
    return {
        "id": hito.id,
        "tipo": hito.tipo.value,
        "titulo": hito.titulo,
        "descripcion": hito.descripcion,
        "fecha_inicio": hito.fecha_inicio.isoformat() if hito.fecha_inicio else None,
        "fecha_fin": hito.fecha_fin.isoformat() if hito.fecha_fin else None,
        "completado": hito.completado,
    }


@router.patch("/{opp_id}/milestones/{hito_id}")
def update_milestone(
    opp_id: int,
    hito_id: int,
    body: MilestoneUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    hito = db.query(Milestone).filter(
        Milestone.id == hito_id, Milestone.opportunity_id == opp_id
    ).first()
    if not hito:
        raise HTTPException(status_code=404, detail="Hito no encontrado")

    if body.titulo is not None:       hito.titulo = body.titulo
    if body.descripcion is not None:  hito.descripcion = body.descripcion
    if body.fecha_inicio is not None: hito.fecha_inicio = body.fecha_inicio
    if body.fecha_fin is not None:    hito.fecha_fin = body.fecha_fin
    if body.completado is not None:   hito.completado = body.completado

    db.commit()
    db.refresh(hito)
    return {
        "id": hito.id,
        "tipo": hito.tipo.value,
        "titulo": hito.titulo,
        "descripcion": hito.descripcion,
        "fecha_inicio": hito.fecha_inicio.isoformat() if hito.fecha_inicio else None,
        "fecha_fin": hito.fecha_fin.isoformat() if hito.fecha_fin else None,
        "completado": hito.completado,
    }


@router.delete("/{opp_id}/milestones/{hito_id}", status_code=204)
def delete_milestone(
    opp_id: int,
    hito_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    hito = db.query(Milestone).filter(
        Milestone.id == hito_id, Milestone.opportunity_id == opp_id
    ).first()
    if not hito:
        raise HTTPException(status_code=404, detail="Hito no encontrado")
    db.delete(hito)
    db.commit()


# ══════════════════════════════════════════════════════════════════
# NOTAS DE ACTIVIDAD
# ══════════════════════════════════════════════════════════════════

@router.post("/{opp_id}/notes", status_code=201)
def add_note(
    opp_id: int,
    body: ActivityNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")

    nota = ActivityNote(
        opportunity_id=opp_id,
        contenido=body.contenido,
        autor=current_user.email,
    )
    db.add(nota)
    db.commit()
    db.refresh(nota)
    return {
        "id": nota.id,
        "contenido": nota.contenido,
        "autor": nota.autor,
        "creado_en": nota.creado_en.isoformat() if nota.creado_en else None,
    }


# ══════════════════════════════════════════════════════════════════
# GENERAR PDF DESDE OPORTUNIDAD
# ══════════════════════════════════════════════════════════════════

@router.post("/{opp_id}/generate-pdf")
def generate_pdf_from_opportunity(
    opp_id: int,
    body: GeneratePDFRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Genera el PDF de propuesta directamente desde una oportunidad.
    Usa los servicios y cliente ya vinculados. Guarda el path en la oportunidad.
    """
    opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")

    cliente = opp.cliente
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    # Servicios vinculados
    service_ids = []
    if opp.service_ids_str:
        service_ids = [int(x) for x in opp.service_ids_str.split(",") if x.strip().isdigit()]

    servicios = []
    if service_ids:
        servicios = db.query(Service).filter(Service.id.in_(service_ids)).all()

    # Servicios en formato para el generador
    # valor_uf de la oportunidad se distribuye si base_price no está definido
    valor_uf_opp = opp.valor_uf or 0.0
    servicios_pdf = [
        {
            "nombre": s.name,
            "descripcion": s.description or "",
            "base_price": s.base_price or 0,
        }
        for s in servicios
    ]
    # Si ningún servicio tiene precio propio pero la oportunidad tiene valor_uf,
    # usarlo como referencia en la tabla
    total_base = sum(s.get("base_price", 0) for s in servicios_pdf)
    if total_base == 0 and valor_uf_opp > 0 and len(servicios_pdf) > 0:
        # Distribuir el valor_uf de la oportunidad proporcionalmente
        por_servicio = round(valor_uf_opp / len(servicios_pdf), 1)
        for s in servicios_pdf:
            s["base_price"] = por_servicio

    # Textos: IA o genéricos
    if body.usar_ia and servicios:
        try:
            textos = generar_textos_completos(
                empresa_cliente=cliente.company_name,
                industria=cliente.industry or "tecnología",
                servicios=[s.name for s in servicios],
                antecedente=body.antecedente or ""
            )
        except Exception:
            textos = _textos_genericos(cliente, servicios)
    else:
        textos = _textos_genericos(cliente, servicios)

    # Construir data
    nombres_srvs = ", ".join(s.name for s in servicios) if servicios else "Servicios de Ciberseguridad"
    data = {
        "titulo_proyecto": opp.titulo,
        "titulo_portada_servicios": opp.titulo,
        "preparado_para": f"{cliente.contact_name} — {cliente.company_name}",
        "objetivo": (
            f"Fortalecer la ciberseguridad de {cliente.company_name} "
            "mediante soluciones especializadas y cumplimiento normativo."
        ),
        "logo_cliente": body.logo_cliente_path,
        "introduccion": textos["introduccion"],
        "frase_clave": textos["frase_clave"],
        "alcance_intro": textos["alcance_intro"],
        "valor_estrategico": textos["valor_estrategico"],
        "cierre_intro": textos["cierre_intro"],
        "antecedente_titulo": None,
        "antecedente_descripcion": "",
        "antecedente_bullets": [],
        "servicios": servicios_pdf,
        "cumplimiento": {
            "intro": "Alineación con el marco legal chileno y estándares internacionales.",
            "bullets": [
                "Ley 21.459 (Delitos Informáticos): Cumplimiento de protocolos de preservación de evidencia.",
                "Ley 19.628 (Protección de la Vida Privada): Gestión segura de datos sensibles.",
                "Alineación ISO 27001: Controles de seguridad bajo estándares globales.",
            ],
        },
        "matriz_valor": [
            {
                "servicio": s.name,
                "beneficio": "Protección Integral",
                "valor_agregado": "Mejora la resiliencia y postura de seguridad organizacional.",
            }
            for s in servicios
        ],
        "metodologia": [
            "Diagnóstico Inicial: Evaluación del estado actual de seguridad.",
            "Plan de Mitigación: Priorización de controles según nivel de riesgo.",
            "Monitoreo y Reporte: Informes ejecutivos periódicos del estado de seguridad.",
        ],
        "diferenciadores": [
            f"Conocimiento de la industria {cliente.industry or 'del cliente'}: soluciones adaptadas al contexto.",
            "Alineación con el CSIRT Nacional: coordinación con organismos de ciberseguridad de Chile.",
        ],
        "valor_uf_oportunidad": valor_uf_opp,
        "nota_costos": "Valores referenciales. Costos definitivos a confirmar tras reunión de alcance.",
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

    # Generar PDF
    nombre = f"propuesta_{cliente.company_name.replace(' ', '_')}_{uuid.uuid4().hex[:8]}.pdf"
    output_dir = os.path.join(
        os.path.dirname(__file__), "..", "..", "propuestas_generadas"
    )
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, nombre)

    try:
        generar_propuesta(data, output_path, usar_ia=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando PDF: {e}")

    # Guardar path en la oportunidad
    opp.pdf_path = output_path
    opp.actualizado_en = datetime.utcnow()
    db.commit()

    return FileResponse(
        path=output_path,
        media_type="application/pdf",
        filename=nombre,
        headers={"Content-Disposition": f"attachment; filename={nombre}"},
    )
