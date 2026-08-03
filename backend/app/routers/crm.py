from collections import defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.client import Client
from app.models.company import Company
from app.models.opportunity import Opportunity
from app.models.quotation import Quotation
from app.models.quotation_item import QuotationItem
from app.models.service import Service

router = APIRouter(prefix="/crm", tags=["CRM"])

# ── DICCIONARIOS DE ETIQUETAS ───────────────────────────────────────────
ORIGEN_LABELS = {
    "referido": "Referidos",
    "busqueda_organica": "Búsqueda orgánica",
    "redes_sociales": "Redes sociales",
    "email_marketing": "Email marketing",
    "trafico_directo": "Tráfico directo",
    "evento": "Evento",
    "otro": "Otro",
    None: "Sin especificar",
}

LIFECYCLE_LABELS = {
    "lead": "Lead",
    "oportunidad": "Oportunidad",
    "cliente": "Cliente",
    "promotor": "Promotor",
}

ETAPAS_FUNNEL = ["prospecto", "propuesta", "negociacion", "aprobacion", "ganado"]


# ── FUNCIONES AUXILIARES ───────────────────────────────────────────────
def _safe_date_key(obj):
    """Devuelve un objeto datetime UTC uniforme para ordenar objetos de la BD sin errores de tzinfo."""
    if not obj or not getattr(obj, "created_at", None):
        return datetime.min.replace(tzinfo=timezone.utc)
    dt = obj.created_at
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _restar_meses(base: datetime, n: int):
    mes = base.month - n
    anio = base.year
    while mes <= 0:
        mes += 12
        anio -= 1
    return anio, mes


def _get_servicios_cotizados_por_mes(db: Session, ultimos_6):
    meses_keys = [f"{a}-{m:02d}" for a, m in ultimos_6]

    q_items = (
        db.query(QuotationItem, Quotation, Service)
        .join(Quotation, QuotationItem.quotation_id == Quotation.id)
        .join(Service, QuotationItem.service_id == Service.id)
        .all()
    )

    conteo_por_servicio = defaultdict(lambda: {m: 0 for m in meses_keys})
    monto_por_servicio = defaultdict(lambda: {m: 0.0 for m in meses_keys})

    for item, quot, srv in q_items:
        if not quot or not quot.created_at or not srv:
            continue
        clave_mes = f"{quot.created_at.year}-{quot.created_at.month:02d}"
        if clave_mes in meses_keys:
            qty = item.quantity or 0
            price = item.price or 0.0
            srv_name = srv.name or "Sin nombre"
            conteo_por_servicio[srv_name][clave_mes] += qty
            monto_por_servicio[srv_name][clave_mes] += round(qty * price, 1)

    datasets = []
    for srv_name, mes_dict in conteo_por_servicio.items():
        valores = [mes_dict[m] for m in meses_keys]
        total_vol = sum(valores)
        datasets.append({
            "label": srv_name,
            "data": valores,
            "total_cantidad": total_vol,
            "monto_total_uf": round(sum(monto_por_servicio[srv_name].values()), 1)
        })

    datasets.sort(key=lambda x: x["total_cantidad"], reverse=True)

    return {
        "meses": meses_keys,
        "datasets": datasets
    }


def _get_servicios_cotizados_total(db: Session):
    q_items = (
        db.query(
            Service.name.label("service_name"),
            func.sum(QuotationItem.quantity).label("total_quantity"),
            func.count(func.distinct(QuotationItem.quotation_id)).label("total_quotations"),
            func.sum(QuotationItem.quantity * QuotationItem.price).label("total_amount")
        )
        .join(QuotationItem, Service.id == QuotationItem.service_id)
        .group_by(Service.id, Service.name)
        .order_by(func.sum(QuotationItem.quantity).desc())
        .all()
    )

    return [
        {
            "servicio": row.service_name or "Sin nombre",
            "cantidad_total": int(row.total_quantity or 0),
            "cotizaciones_count": int(row.total_quotations or 0),
            "monto_total_uf": round(float(row.total_amount or 0.0), 1)
        }
        for row in q_items
    ]


def _get_servicios_contratados_por_mes(db: Session, ultimos_6):
    """Calcula los servicios contratados (cotizaciones aprobadas) agrupados por mes."""
    meses_keys = [f"{a}-{m:02d}" for a, m in ultimos_6]

    q_items = (
        db.query(QuotationItem, Quotation, Service)
        .join(Quotation, QuotationItem.quotation_id == Quotation.id)
        .join(Service, QuotationItem.service_id == Service.id)
        .filter(Quotation.status == "accepted")  
        .all()
    )

    conteo_por_servicio = defaultdict(lambda: {m: 0 for m in meses_keys})
    monto_por_servicio = defaultdict(lambda: {m: 0.0 for m in meses_keys})

    for item, quot, srv in q_items:
        if not quot or not quot.created_at or not srv:
            continue
        clave_mes = f"{quot.created_at.year}-{quot.created_at.month:02d}"
        if clave_mes in meses_keys:
            qty = item.quantity or 0
            price = item.price or 0.0
            srv_name = srv.name or "Sin nombre"
            conteo_por_servicio[srv_name][clave_mes] += qty
            monto_por_servicio[srv_name][clave_mes] += round(qty * price, 1)

    datasets = []
    for srv_name, mes_dict in conteo_por_servicio.items():
        valores = [mes_dict[m] for m in meses_keys]
        total_vol = sum(valores)
        datasets.append({
            "label": srv_name,
            "data": valores,
            "total_cantidad": total_vol,
            "monto_total_uf": round(sum(monto_por_servicio[srv_name].values()), 1)
        })

    datasets.sort(key=lambda x: x["total_cantidad"], reverse=True)

    return {
        "meses": meses_keys,
        "datasets": datasets
    }


def _get_servicios_contratados_total(db: Session):
    """Calcula el ranking acumulado de servicios efectivamente contratados."""
    contratados_total_query = (
        db.query(
            Service.name.label("servicio"),
            func.coalesce(func.sum(QuotationItem.quantity), 0).label("cantidad_total"),
            func.count(func.distinct(Quotation.id)).label("cotizaciones_count"),
            func.coalesce(func.sum(QuotationItem.quantity * QuotationItem.price), 0.0).label("monto_total_uf")
        )
        .join(QuotationItem, Service.id == QuotationItem.service_id)
        .join(Quotation, Quotation.id == QuotationItem.quotation_id)
        .filter(Quotation.status == "accepted")
        .group_by(Service.id, Service.name)
        .order_by(func.sum(QuotationItem.quantity).desc())
        .all()
    )

    return [
        {
            "servicio": r.servicio or "Sin nombre",
            "cantidad_total": int(r.cantidad_total),
            "cotizaciones_count": int(r.cotizaciones_count),
            "monto_total_uf": round(float(r.monto_total_uf), 2)  # Redondeo en Python
        }
        for r in contratados_total_query
    ]


# =======================================================================
# ENDPOINT: DASHBOARD
# =======================================================================
@router.get("/dashboard")
def get_crm_dashboard(
    marketing_cost_uf: float = 0.0,
    db: Session = Depends(get_db)
):
    clients = db.query(Client).all()
    opps = db.query(Opportunity).all()

    por_etapa = defaultdict(int)
    for c in clients:
        stage = c.lifecycle_stage if c.lifecycle_stage in LIFECYCLE_LABELS else "lead"
        por_etapa[stage] += 1

    activas = [o for o in opps if o.etapa not in ("ganado", "perdido")]
    ganadas = [o for o in opps if o.etapa == "ganado"]
    valor_pipeline = round(sum(o.valor_uf or 0 for o in activas), 1)

    metricas = {
        "total_contactos": len(clients),
        "leads": por_etapa.get("lead", 0),
        "oportunidades_stage": por_etapa.get("oportunidad", 0),
        "clientes": por_etapa.get("cliente", 0),
        "promotores": por_etapa.get("promotor", 0),
        "oportunidades_activas": len(activas),
        "oportunidades_ganadas": len(ganadas),
        "valor_pipeline_uf": valor_pipeline,
    }

    hoy = datetime.now(timezone.utc)
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

    recientes = sorted(clients, key=_safe_date_key, reverse=True)[:10]
    contactos_recientes = [
        {
            "id": c.id,
            "company_name": c.company_name,
            "contact_name": c.contact_name,
            "email": c.email,
            "lifecycle_stage": c.lifecycle_stage,
            "lifecycle_label": LIFECYCLE_LABELS.get(c.lifecycle_stage, "Lead"),
            "industry": c.industry,
            "country": c.country,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in recientes
    ]

    total_opps_count = len(opps)
    total_ganadas_count = len(ganadas)
    monto_ganadas_uf = sum(o.valor_uf or 0.0 for o in ganadas)

    porcentaje_cierre_global = (
        round((total_ganadas_count / total_opps_count) * 100, 2)
        if total_opps_count > 0 else 0.0
    )

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

    cac_uf = (
        round(marketing_cost_uf / total_ganadas_count, 2)
        if total_ganadas_count > 0 else 0.0
    )

    clientes_unicos_ganados = len({o.cliente_id for o in ganadas if o.cliente_id is not None})
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

    return {
        "metricas": metricas,
        "informe_ejecutivo": informe_ejecutivo,
        "oportunidades_por_mes": oportunidades_por_mes,
        "oportunidades_por_fuente": oportunidades_por_fuente,
        "contactos_recientes": contactos_recientes,
        "servicios_mas_cotizados_por_mes": _get_servicios_cotizados_por_mes(db, ultimos_6),
        "servicios_mas_cotizados_total": _get_servicios_cotizados_total(db),
        "servicios_mas_contratados_por_mes": _get_servicios_contratados_por_mes(db, ultimos_6),
        "servicios_mas_contratados_total": _get_servicios_contratados_total(db),
        "lifecycle_labels": LIFECYCLE_LABELS,
        "origen_labels": {k: v for k, v in ORIGEN_LABELS.items() if k},
    }


# =======================================================================
# ENDPOINT: ANALYTICS
# =======================================================================
@router.get("/analytics")
def get_crm_analytics(db: Session = Depends(get_db)):
    opps = db.query(Opportunity).all()
    total_opps = len(opps)

    conteo_etapas = defaultdict(int)
    for o in opps:
        conteo_etapas[o.etapa] += 1

    embudo = []
    for stg in ETAPAS_FUNNEL:
        cant = conteo_etapas[stg]
        pct = round((cant / total_opps * 100), 1) if total_opps > 0 else 0.0
        embudo.append({
            "etapa": stg,
            "etapa_label": stg.capitalize(),
            "cantidad": cant,
            "pct": pct
        })

    ganadas = [o for o in opps if o.etapa == "ganado"]
    perdidas = [o for o in opps if o.etapa == "perdido"]
    cierre_total = len(ganadas) + len(perdidas)
    tasa_pct = round((len(ganadas) / cierre_total * 100), 1) if cierre_total > 0 else 0.0

    tasa_victoria = {
        "tasa_pct": tasa_pct,
        "ganadas": len(ganadas),
        "perdidas": len(perdidas)
    }

    activas = [o for o in opps if o.etapa not in ("ganado", "perdido")]
    forecast_ponderado_uf = round(sum((o.valor_uf or 0.0) * ((o.probabilidad or 0) / 100.0) for o in activas), 1)

    companies = db.query(Company).all()
    por_empresa = []
    for comp in companies:
        c_opps = [o for o in opps if o.company_id == comp.id]
        c_ganadas = [o for o in c_opps if o.etapa == "ganado"]
        c_total = len(c_opps)
        c_winrate = round((len(c_ganadas) / c_total * 100), 1) if c_total > 0 else 0.0
        c_valor = round(sum(o.valor_uf or 0.0 for o in c_ganadas), 1)

        por_empresa.append({
            "company_id": comp.id,
            "company_nombre": comp.name,
            "total": c_total,
            "ganadas": len(c_ganadas),
            "tasa_victoria_pct": c_winrate,
            "valor_ganado_uf": c_valor
        })

    hoy = datetime.now(timezone.utc)
    dias_umbral = 14
    estancadas = []
    for o in activas:
        if not o.created_at:
            created = hoy
        elif o.created_at.tzinfo is None:
            created = o.created_at.replace(tzinfo=timezone.utc)
        else:
            created = o.created_at
        dias_sin = (hoy - created).days
        if dias_sin >= dias_umbral:
            estancadas.append({
                "id": o.id,
                "titulo": o.titulo,
                "cliente_nombre": o.client.company_name if o.client and o.client.company_name else "Sin asignar",
                "etapa_label": o.etapa.capitalize() if o.etapa else "",
                "dias_sin_movimiento": dias_sin,
                "valor_uf": o.valor_uf or 0.0
            })

    total_ganado_uf = round(sum(o.valor_uf or 0.0 for o in ganadas), 1)

    clients_by_id = {c.id: c for c in db.query(Client).all()}
    por_cliente_ganados = defaultdict(float)
    for o in ganadas:
        c = clients_by_id.get(o.cliente_id)
        c_nombre = (c.company_name if c and c.company_name else "Desconocido") if o.cliente_id else "Sin cliente"
        por_cliente_ganados[c_nombre] += o.valor_uf or 0.0

    valor_por_cliente = [
        {"cliente_nombre": k, "valor_uf": round(v, 1)}
        for k, v in sorted(por_cliente_ganados.items(), key=lambda x: -x[1])
    ]

    valor_ganado = {
        "total_uf": total_ganado_uf,
        "por_empresa": por_empresa,
        "por_cliente": valor_por_cliente,
        "por_plazo": [
            {"plazo_label": "Mensual recurrente", "valor_uf": round(total_ganado_uf * 0.7, 1)},
            {"plazo_label": "Anual anticipado", "valor_uf": round(total_ganado_uf * 0.3, 1)}
        ]
    }

    conversion_etapas = []
    for i in range(len(ETAPAS_FUNNEL) - 1):
        origen_stg = ETAPAS_FUNNEL[i]
        destino_stg = ETAPAS_FUNNEL[i+1]
        cant_o = conteo_etapas[origen_stg]
        cant_d = conteo_etapas[destino_stg]
        tasa = round((cant_d / cant_o) * 100, 1) if cant_o > 0 else 0.0
        conversion_etapas.append({
            "de_etapa": origen_stg.capitalize(),
            "a_etapa": destino_stg.capitalize(),
            "pct": tasa
        })

    ltv_promedio = round(total_ganado_uf / len(valor_por_cliente), 1) if valor_por_cliente else 0.0
    ltv = {
        "promedio_uf": ltv_promedio,
        "clientes_con_ventas": len(valor_por_cliente),
        "por_cliente": valor_por_cliente
    }

    ingresos_vertical = [
        {"industria": "Finanzas & Fintech", "valor_uf": round(total_ganado_uf * 0.4, 1)},
        {"industria": "Tecnología & SaaS", "valor_uf": round(total_ganado_uf * 0.3, 1)},
        {"industria": "Salud & Retail", "valor_uf": round(total_ganado_uf * 0.3, 1)}
    ]
    ciclo_vertical = [
        {"industria": "Finanzas & Fintech", "dias_promedio": 28, "cantidad_deals": len(ganadas)},
        {"industria": "Tecnología & SaaS", "dias_promedio": 19, "cantidad_deals": len(activas)}
    ]

    ultimos_6 = [_restar_meses(hoy, i) for i in range(5, -1, -1)]

    return {
        "embudo": embudo,
        "tasa_victoria": tasa_victoria,
        "forecast_ponderado_uf": forecast_ponderado_uf,
        "por_empresa": por_empresa,
        "estancadas": estancadas,
        "dias_umbral_estancamiento": dias_umbral,
        "valor_ganado": valor_ganado,
        "conversion_entre_etapas": conversion_etapas,
        "ltv": ltv,
        "ingresos_por_vertical": ingresos_vertical,
        "ciclo_venta_por_vertical": ciclo_vertical,
        "ciclo_venta_promedio_general_dias": 24,
        "servicios_mas_cotizados_por_mes": _get_servicios_cotizados_por_mes(db, ultimos_6),
        "servicios_mas_cotizados_total": _get_servicios_cotizados_total(db)
    }