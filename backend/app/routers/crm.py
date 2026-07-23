from datetime import datetime
from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.client import Client
from app.models.opportunity import Opportunity

router = APIRouter(prefix="/crm", tags=["CRM"])

ORIGEN_LABELS = {
    "referido":          "Referidos",
    "busqueda_organica": "Búsqueda orgánica",
    "redes_sociales":    "Redes sociales",
    "email_marketing":   "Email marketing",
    "trafico_directo":   "Tráfico directo",
    "evento":            "Evento",
    "otro":              "Otro",
    None:                "Sin especificar",
}

LIFECYCLE_LABELS = {
    "lead":        "Lead",
    "oportunidad": "Oportunidad",
    "cliente":     "Cliente",
    "promotor":    "Promotor",
}


@router.get("/dashboard")
def get_crm_dashboard(db: Session = Depends(get_db)):
    clients = db.query(Client).all()
    opps    = db.query(Opportunity).all()

    # ── Métricas principales ────────────────────────────────────────
    por_etapa = defaultdict(int)
    for c in clients:
        stage = c.lifecycle_stage if c.lifecycle_stage in LIFECYCLE_LABELS else "lead"
        por_etapa[stage] += 1

    activas = [o for o in opps if o.etapa not in ("ganado", "perdido")]
    ganadas = [o for o in opps if o.etapa == "ganado"]
    valor_pipeline = round(sum(o.valor_uf or 0 for o in activas), 1)

    metricas = {
        "total_contactos":       len(clients),
        "leads":                 por_etapa.get("lead", 0),
        "oportunidades_stage":   por_etapa.get("oportunidad", 0),
        "clientes":              por_etapa.get("cliente", 0),
        "promotores":            por_etapa.get("promotor", 0),
        "oportunidades_activas": len(activas),
        "oportunidades_ganadas": len(ganadas),
        "valor_pipeline_uf":     valor_pipeline,
    }

    # ── Oportunidades en el tiempo (últimos 6 meses) ────────────────
    hoy = datetime.utcnow()

    def _restar_meses(base: datetime, n: int):
        mes = base.month - n
        anio = base.year
        while mes <= 0:
            mes += 12
            anio -= 1
        return anio, mes

    ultimos_6 = [_restar_meses(hoy, i) for i in range(5, -1, -1)]
    conteo_mes = {f"{a}-{m:02d}": 0 for a, m in ultimos_6}

    for o in opps:
        if not o.created_at:
            continue
        clave = f"{o.created_at.year}-{o.created_at.month:02d}"
        if clave in conteo_mes:
            conteo_mes[clave] += 1

    oportunidades_por_mes = [
        {"mes": f"{a}-{m:02d}", "cantidad": conteo_mes[f"{a}-{m:02d}"]}
        for a, m in ultimos_6
    ]

    # ── Oportunidades por fuente (origen del cliente) ───────────────
    clientes_by_id = {c.id: c for c in clients}
    por_fuente = defaultdict(int)
    for o in opps:
        cliente = clientes_by_id.get(o.cliente_id)
        origen = cliente.origen if cliente else None
        origen = origen if origen in ORIGEN_LABELS else None
        por_fuente[origen] += 1

    oportunidades_por_fuente = [
        {"origen": ORIGEN_LABELS[k], "cantidad": v}
        for k, v in sorted(por_fuente.items(), key=lambda x: -x[1])
    ]

    # ── Contactos recientes ──────────────────────────────────────────
    recientes = sorted(
        clients, key=lambda c: c.created_at or datetime.min, reverse=True
    )[:10]
    contactos_recientes = [
        {
            "id":              c.id,
            "company_name":    c.company_name,
            "contact_name":    c.contact_name,
            "email":           c.email,
            "lifecycle_stage": c.lifecycle_stage,
            "lifecycle_label": LIFECYCLE_LABELS.get(c.lifecycle_stage, "Lead"),
            "industry":        c.industry,
            "country":         c.country,
            "created_at":      c.created_at.isoformat() if c.created_at else None,
        }
        for c in recientes
    ]

    return {
        "metricas":                 metricas,
        "oportunidades_por_mes":    oportunidades_por_mes,
        "oportunidades_por_fuente": oportunidades_por_fuente,
        "contactos_recientes":      contactos_recientes,
        "lifecycle_labels":         LIFECYCLE_LABELS,
        "origen_labels":            {k: v for k, v in ORIGEN_LABELS.items() if k},
    }
