from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.opportunity import Opportunity
from app.models.milestone import Milestone
from app.models.client import Client
from app.models.company import Company
from app.schemas.opportunity import (
    OpportunityCreate, OpportunityPatch, OpportunityResponse,
    MilestoneCreate
)

router = APIRouter(prefix="/opportunities", tags=["Opportunities"])

ETAPA_ORDER = ["prospecto","propuesta","negociacion","aprobacion","ganado","perdido"]


def _enrich(opp: Opportunity, db: Session) -> dict:
    """Añade cliente_nombre y company_nombre al dict de la oportunidad."""
    data = {
        "id":             opp.id,
        "cliente_id":     opp.cliente_id,
        "company_id":     opp.company_id,
        "titulo":         opp.titulo,
        "etapa":          opp.etapa,
        "probabilidad":   opp.probabilidad,
        "valor_uf":       opp.valor_uf,
        "plazo_meses":    opp.plazo_meses,
        "notas":          opp.notas,
        "cliente_nombre": opp.client.company_name if opp.client else "",
        "company_nombre": opp.company.name if opp.company else None,
        "hitos": [
            {
                "id":             h.id,
                "opportunity_id": h.opportunity_id,
                "tipo":           h.tipo,
                "titulo":         h.titulo,
                "descripcion":    h.descripcion,
                "completado":     h.completado,
                "fecha_inicio":   h.fecha_inicio.isoformat() if h.fecha_inicio else None,
                "fecha_fin":      h.fecha_fin.isoformat()    if h.fecha_fin    else None,
            }
            for h in opp.milestones
        ],
    }
    return data


def _avanzar_lifecycle(client: Client, hacia: str, db: Session):
    """
    Avanza la etapa del ciclo de vida de un cliente, solo si:
    - lifecycle_auto está activado (el cliente no está "congelado" a mano), y
    - la nueva etapa es un avance real (no retrocede a un cliente que ya
      esté más adelante, ej. no baja a un "cliente" de vuelta a "oportunidad").
    """
    ORDEN = ["lead", "oportunidad", "cliente", "promotor"]
    if not client or not client.lifecycle_auto:
        return
    actual = client.lifecycle_stage if client.lifecycle_stage in ORDEN else "lead"
    if hacia not in ORDEN:
        return
    if ORDEN.index(hacia) > ORDEN.index(actual):
        client.lifecycle_stage = hacia
        db.add(client)


# ── CRUD Oportunidades ─────────────────────────────────────────────────────

@router.post("/", status_code=201)
def create_opportunity(body: OpportunityCreate, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == body.cliente_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    if body.company_id is not None:
        company = db.query(Company).filter(Company.id == body.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Empresa emisora no encontrada")
    opp = Opportunity(**body.model_dump())
    db.add(opp)

    # CRM: crear una oportunidad avanza al cliente de "lead" a "oportunidad" (si aplica)
    _avanzar_lifecycle(client, "oportunidad", db)

    db.commit()
    db.refresh(opp)
    return _enrich(opp, db)


@router.get("/pipeline")
def get_pipeline(company_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(Opportunity)
    if company_id is not None:
        query = query.filter(Opportunity.company_id == company_id)
    opps = query.all()

    pipeline = {e: [] for e in ETAPA_ORDER}
    for opp in opps:
        etapa = opp.etapa if opp.etapa in pipeline else "prospecto"
        pipeline[etapa].append(_enrich(opp, db))

    activas   = [o for o in opps if o.etapa not in ("ganado","perdido")]
    ganadas   = [o for o in opps if o.etapa == "ganado"]
    valor_tot = sum(o.valor_uf for o in activas)
    prob_prom = round(sum(o.probabilidad for o in activas) / len(activas), 1) if activas else 0

    metricas = {
        "total_activas":        len(activas),
        "total_ganadas":        len(ganadas),
        "valor_pipeline_uf":    round(valor_tot, 1),
        "probabilidad_promedio": prob_prom,
    }
    return {"pipeline": pipeline, "metricas": metricas}


@router.get("/{opp_id}")
def get_opportunity(opp_id: int, db: Session = Depends(get_db)):
    opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    return _enrich(opp, db)


@router.patch("/{opp_id}")
def patch_opportunity(opp_id: int, body: OpportunityPatch, db: Session = Depends(get_db)):
    opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    data = body.model_dump(exclude_none=True)
    if "company_id" in data and data["company_id"] is not None:
        company = db.query(Company).filter(Company.id == data["company_id"]).first()
        if not company:
            raise HTTPException(status_code=404, detail="Empresa emisora no encontrada")
    for field, value in data.items():
        setattr(opp, field, value)

    # CRM: si la oportunidad se marca como "ganado", el cliente pasa a "cliente"
    if data.get("etapa") == "ganado":
        client = db.query(Client).filter(Client.id == opp.cliente_id).first()
        _avanzar_lifecycle(client, "cliente", db)

    db.commit()
    db.refresh(opp)
    return _enrich(opp, db)


@router.delete("/{opp_id}", status_code=204)
def delete_opportunity(opp_id: int, db: Session = Depends(get_db)):
    opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    db.delete(opp)
    db.commit()


# ── Milestones ─────────────────────────────────────────────────────────────

@router.post("/{opp_id}/milestones", status_code=201)
def add_milestone(opp_id: int, body: MilestoneCreate, db: Session = Depends(get_db)):
    opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    ms = Milestone(opportunity_id=opp_id, **body.model_dump())
    db.add(ms)
    db.commit()
    db.refresh(ms)
    return {
        "id":             ms.id,
        "opportunity_id": ms.opportunity_id,
        "tipo":           ms.tipo,
        "titulo":         ms.titulo,
        "descripcion":    ms.descripcion,
        "completado":     ms.completado,
        "fecha_inicio":   ms.fecha_inicio.isoformat() if ms.fecha_inicio else None,
        "fecha_fin":      ms.fecha_fin.isoformat()    if ms.fecha_fin    else None,
    }
