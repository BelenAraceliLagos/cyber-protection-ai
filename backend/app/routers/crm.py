from datetime import datetime
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.models.client import Client
from app.models.opportunity import Opportunity

router = APIRouter(prefix="/crm", tags=["CRM"])

# ── DICCIONARIOS DE ETIQUETAS ───────────────────────────────────────────
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

ETAPAS_FUNNEL = ["prospecto", "propuesta", "negociacion", "aprobacion", "ganado"]


# ── ESQUEMA PYDANTIC PARA CAPTURA WEB ─────────────────────────────────
class WebLeadSchema(BaseModel):
    contact_name: str
    email: EmailStr
    company_name: str
    phone: str | None = None
    origen: str = "busqueda_organica"
    valor_estimado_uf: float = 0.0
    notas: str | None = None


# =======================================================================
# 1. ENDPOINT PÚBLICO: CAPTURA DE LEADS DESDE LA PÁGINA WEB
# =======================================================================
@router.post("/public/lead")
def receive_web_lead(lead: WebLeadSchema, db: Session = Depends(get_db)):
    """
    Endpoint sin autenticación para registrar prospectos desde el formulario de la web.
    Ruta final: POST http://localhost:8080/crm/public/lead
    """
    # 1. Buscar o crear el Cliente
    client = db.query(Client).filter(Client.email == lead.email).first()
    
    if not client:
        client = Client(
            contact_name=lead.contact_name,
            email=lead.email,
            company_name=lead.company_name,
            phone=lead.phone,
            origen=lead.origen if lead.origen in ORIGEN_LABELS else "busqueda_organica",
            lifecycle_stage="lead"
        )
        db.add(client)
        db.commit()
        db.refresh(client)
    else:
        client.lifecycle_stage = "oportunidad"
        db.commit()

    # 2. Crear Oportunidad inicial en etapa 'prospecto'
    new_opportunity = Opportunity(
        cliente_id=client.id,
        titulo=f"Lead Web - {lead.company_name}",
        etapa="prospecto",
        probabilidad=30,
        valor_uf=lead.valor_estimado_uf,
        notas=lead.notas or "Ingresado automáticamente desde la página web."
    )
    db.add(new_opportunity)
    db.commit()

    return {
        "status": "success",
        "message": "Lead registrado en el CRM correctamente",
        "client_id": client.id,
        "opportunity_id": new_opportunity.id
    }


# =======================================================================
# 2. ENDPOINT PRIVADO: DASHBOARD COMPLETO CON METRICAS EJECUTIVAS
# =======================================================================
@router.get("/dashboard")
def get_crm_dashboard(
    marketing_cost_uf: float = 0.0,  # Opcional: costo Mkt/Ventas para calcular CAC
    db: Session = Depends(get_db)
):
    """
    Entrega el resumen del CRM + Informe Ejecutivo (Funnel, CAC, LTV, Conversión).
    Ruta final: GET http://localhost:8080/crm/dashboard
    """
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

    # ── METRICAS EJECUTIVAS: FUNNEL, CONVERSIÓN, CAC Y LTV ────────────
    total_opps_count = len(opps)
    total_ganadas_count = len(ganadas)
    monto_ganadas_uf = sum(o.valor_uf or 0.0 for o in ganadas)

    # 1. Porcentaje global de cierre
    porcentaje_cierre_global = (
        round((total_ganadas_count / total_opps_count) * 100, 2)
        if total_opps_count > 0 else 0.0
    )

    # 2. Conversión entre etapas del Funnel
    conteo_etapas = defaultdict(int)
    for o in opps:
        conteo_etapas[o.etapa] += 1

    conversion_etapas = []
    for i in range(len(ETAPAS_FUNNEL) - 1):
        origen_stg = ETAPAS_FUNNEL[i]
        destino_stg = ETAPAS_FUNNEL[i+1]
        
        cant_origen = conteo_etapas[origen_stg]
        cant_destino = conteo_etapas[destino_stg]
        
        tasa = round((cant_destino / cant_origen) * 100, 2) if cant_origen > 0 else 0.0
        conversion_etapas.append({
            "de_etapa": origen_stg.capitalize(),
            "a_etapa": destino_stg.capitalize(),
            "porcentaje_conversion": tasa
        })

    # 3. CAC (Costo de Adquisición de Clientes en UF)
    cac_uf = (
        round(marketing_cost_uf / total_ganadas_count, 2)
        if total_ganadas_count > 0 else 0.0
    )

    # 4. LTV (Lifetime Value Promedio por Cliente Único en UF)
    clientes_unicos_ganados = len({o.cliente_id for o in ganadas})
    ltv_uf = (
        round(monto_ganadas_uf / clientes_unicos_ganados, 2)
        if clientes_unicos_ganados > 0 else 0.0
    )

    informe_ejecutivo = {
        "ventas_ganadas": {
            "cantidad": total_ganadas_count,
            "monto_total_uf": round(monto_ganadas_uf, 2)
        },
        "porcentaje_cierre_global": porcentaje_cierre_global,
        "conversion_entre_etapas": conversion_etapas,
        "cac_uf": cac_uf,
        "ltv_uf": ltv_uf
    }

    # ── RETORNO FINAL ────────────────────────────────────────────────
    return {
        "metricas":                 metricas,
        "informe_ejecutivo":        informe_ejecutivo,
        "oportunidades_por_mes":    oportunidades_por_mes,
        "oportunidades_por_fuente": oportunidades_por_fuente,
        "contactos_recientes":      contactos_recientes,
        "lifecycle_labels":        LIFECYCLE_LABELS,
        "origen_labels":           {k: v for k, v in ORIGEN_LABELS.items() if k},
    }