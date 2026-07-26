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


ETAPA_ORDER = ["prospecto", "propuesta", "negociacion", "aprobacion", "ganado"]
ETAPA_LABELS = {
    "prospecto":   "Prospecto",
    "propuesta":   "Propuesta",
    "negociacion": "Negociación",
    "aprobacion":  "Aprobación",
    "ganado":      "Ganado",
}

DIAS_ESTANCAMIENTO = 14  # a partir de cuántos días sin movimiento se considera "estancada"

PLAZO_LABELS = {
    3:    "3 meses (Plan Flexible)",
    6:    "6 meses (Plan Semestral)",
    9:    "9 meses (Plan Extendido)",
    12:   "12 meses (Plan Anual)",
    None: "Sin especificar",
}


def _valor_total(o: Opportunity) -> float:
    """
    Valor total del contrato: valor mensual × plazo contratado.
    Si no se especificó plazo, se cuenta solo el valor mensual (no se asume
    ningún plazo por defecto, para no inflar ni subestimar el total).
    """
    if o.plazo_meses:
        return (o.valor_uf or 0) * o.plazo_meses
    return o.valor_uf or 0


@router.get("/analytics")
def get_crm_analytics(db: Session = Depends(get_db)):
    from app.models.company import Company

    opps     = db.query(Opportunity).all()
    clients  = {c.id: c for c in db.query(Client).all()}
    companies = {c.id: c for c in db.query(Company).all()}
    hoy = datetime.utcnow()

    # ── 1. Embudo de conversión ──────────────────────────────────────
    # Nota: es un embudo "de foto actual" (cuántas oportunidades están HOY
    # en cada etapa o más adelante), no histórico — para un embudo con el
    # verdadero recorrido de cada oportunidad haría falta guardar el
    # historial de cambios de etapa, que hoy no se registra.
    total_no_perdidas = len([o for o in opps if o.etapa != "perdido"])
    embudo = []
    for idx, etapa in enumerate(ETAPA_ORDER):
        # cuenta las que están en esta etapa o en cualquiera posterior (no perdidas)
        cantidad = len([
            o for o in opps
            if o.etapa != "perdido" and o.etapa in ETAPA_ORDER
            and ETAPA_ORDER.index(o.etapa) >= idx
        ])
        pct = round(cantidad / total_no_perdidas * 100, 1) if total_no_perdidas else 0
        embudo.append({"etapa": etapa, "etapa_label": ETAPA_LABELS[etapa], "cantidad": cantidad, "pct": pct})

    # ── 2. Tasa de victoria ──────────────────────────────────────────
    ganadas  = [o for o in opps if o.etapa == "ganado"]
    perdidas = [o for o in opps if o.etapa == "perdido"]
    cerradas = len(ganadas) + len(perdidas)
    tasa_victoria = {
        "ganadas":  len(ganadas),
        "perdidas": len(perdidas),
        "tasa_pct": round(len(ganadas) / cerradas * 100, 1) if cerradas else 0,
    }

    # ── 3. Forecast ponderado ────────────────────────────────────────
    activas = [o for o in opps if o.etapa not in ("ganado", "perdido")]
    forecast_ponderado_uf = round(
        sum((o.valor_uf or 0) * (o.probabilidad or 0) / 100 for o in activas), 1
    )

    # ── 4. Comparativo por empresa emisora ───────────────────────────
    por_empresa_raw = defaultdict(list)
    for o in opps:
        por_empresa_raw[o.company_id].append(o)

    por_empresa = []
    for company_id, lista in por_empresa_raw.items():
        nombre = companies[company_id].name if company_id and company_id in companies else "Sin asignar"
        g = len([o for o in lista if o.etapa == "ganado"])
        p = len([o for o in lista if o.etapa == "perdido"])
        cerr = g + p
        valor_ganado = sum(_valor_total(o) for o in lista if o.etapa == "ganado")
        por_empresa.append({
            "company_id":       company_id,
            "company_nombre":   nombre,
            "total":            len(lista),
            "ganadas":          g,
            "tasa_victoria_pct": round(g / cerr * 100, 1) if cerr else 0,
            "valor_ganado_uf":  round(valor_ganado, 1),
        })
    por_empresa.sort(key=lambda x: -x["total"])

    # ── 5. Alertas de oportunidades estancadas ───────────────────────
    estancadas = []
    for o in opps:
        if o.etapa in ("ganado", "perdido"):
            continue
        ultimo_movimiento = o.updated_at or o.created_at
        if not ultimo_movimiento:
            continue
        dias = (hoy - ultimo_movimiento.replace(tzinfo=None)).days
        if dias >= DIAS_ESTANCAMIENTO:
            cliente = clients.get(o.cliente_id)
            estancadas.append({
                "id":                o.id,
                "titulo":            o.titulo,
                "cliente_nombre":    cliente.company_name if cliente else "",
                "etapa":             o.etapa,
                "etapa_label":       ETAPA_LABELS.get(o.etapa, o.etapa),
                "dias_sin_movimiento": dias,
                "valor_uf":          o.valor_uf,
            })
    estancadas.sort(key=lambda x: -x["dias_sin_movimiento"])

    # ── 6. Valor ganado: total, por cliente y por plazo contratado ────
    ganadas_opps = [o for o in opps if o.etapa == "ganado"]

    valor_ganado_total_uf = round(sum(_valor_total(o) for o in ganadas_opps), 1)

    por_cliente_raw = defaultdict(float)
    for o in ganadas_opps:
        por_cliente_raw[o.cliente_id] += _valor_total(o)
    valor_ganado_por_cliente = sorted([
        {
            "cliente_id":     cid,
            "cliente_nombre": clients[cid].company_name if cid in clients else "—",
            "valor_uf":       round(v, 1),
        }
        for cid, v in por_cliente_raw.items()
    ], key=lambda x: -x["valor_uf"])

    por_plazo_raw = defaultdict(float)
    for o in ganadas_opps:
        por_plazo_raw[o.plazo_meses] += _valor_total(o)
    orden_plazo = [3, 6, 9, 12, None]
    valor_ganado_por_plazo = [
        {
            "plazo_meses": p,
            "plazo_label": PLAZO_LABELS.get(p, f"{p} meses"),
            "valor_uf":    round(por_plazo_raw.get(p, 0), 1),
        }
        for p in orden_plazo if p in por_plazo_raw
    ]

    valor_ganado = {
        "total_uf":    valor_ganado_total_uf,
        "por_empresa": [
            {"company_id": e["company_id"], "company_nombre": e["company_nombre"], "valor_uf": e["valor_ganado_uf"]}
            for e in por_empresa if e["valor_ganado_uf"] > 0
        ],
        "por_cliente": valor_ganado_por_cliente,
        "por_plazo":   valor_ganado_por_plazo,
    }

    # ── 7. Conversión entre etapas consecutivas ──────────────────────
    # Usa el mismo "embudo de foto actual": de las que llegaron a la etapa
    # N, ¿qué porcentaje llegó también a la etapa N+1? Aquí SÍ se puede
    # calcular con los datos que ya existen (a diferencia de un embudo
    # histórico real), porque solo compara conteos entre etapas vecinas.
    conversion_entre_etapas = []
    for i in range(len(embudo) - 1):
        actual = embudo[i]
        siguiente = embudo[i + 1]
        pct = round(siguiente["cantidad"] / actual["cantidad"] * 100, 1) if actual["cantidad"] else 0
        conversion_entre_etapas.append({
            "de_etapa":     actual["etapa_label"],
            "a_etapa":      siguiente["etapa_label"],
            "pct":          pct,
        })

    # ── 8. LTV (valor histórico total) por cliente ───────────────────
    # Es el mismo cálculo que "valor_ganado.por_cliente" — se muestra acá
    # también con foco explícito en LTV + el promedio general.
    ltv_por_cliente = valor_ganado_por_cliente[:10]  # top 10
    clientes_con_ventas = len(por_cliente_raw)
    ltv_promedio_uf = round(valor_ganado_total_uf / clientes_con_ventas, 1) if clientes_con_ventas else 0

    # ── 9. Ingresos por vertical (industria del cliente) ─────────────
    por_industria_raw = defaultdict(float)
    for o in ganadas_opps:
        cliente = clients.get(o.cliente_id)
        industria = (cliente.industry if cliente and cliente.industry else "Sin especificar")
        por_industria_raw[industria] += _valor_total(o)
    ingresos_por_vertical = sorted([
        {"industria": k, "valor_uf": round(v, 1)}
        for k, v in por_industria_raw.items()
    ], key=lambda x: -x["valor_uf"])

    # ── 10. Ciclo de venta promedio, por vertical ────────────────────
    # Días entre la creación de la oportunidad y su último movimiento,
    # para oportunidades ya cerradas (ganadas o perdidas). Es una
    # aproximación: asumimos que el último cambio registrado coincide con
    # el cierre, ya que no se guarda una fecha de cierre explícita.
    cerradas_opps = [o for o in opps if o.etapa in ("ganado", "perdido")]
    dias_por_industria_raw = defaultdict(list)
    for o in cerradas_opps:
        if not o.created_at or not o.updated_at:
            continue
        dias = (o.updated_at - o.created_at).days
        cliente = clients.get(o.cliente_id)
        industria = (cliente.industry if cliente and cliente.industry else "Sin especificar")
        dias_por_industria_raw[industria].append(dias)

    ciclo_venta_por_vertical = sorted([
        {
            "industria":       k,
            "dias_promedio":   round(sum(v) / len(v), 1),
            "cantidad_deals":  len(v),
        }
        for k, v in dias_por_industria_raw.items()
    ], key=lambda x: -x["dias_promedio"])

    todos_los_dias = [d for lista in dias_por_industria_raw.values() for d in lista]
    ciclo_venta_promedio_general_dias = round(sum(todos_los_dias) / len(todos_los_dias), 1) if todos_los_dias else 0

    return {
        "embudo":                    embudo,
        "conversion_entre_etapas":   conversion_entre_etapas,
        "tasa_victoria":             tasa_victoria,
        "forecast_ponderado_uf":     forecast_ponderado_uf,
        "por_empresa":               por_empresa,
        "estancadas":                estancadas,
        "valor_ganado":              valor_ganado,
        "ltv": {
            "por_cliente":       ltv_por_cliente,
            "promedio_uf":       ltv_promedio_uf,
            "clientes_con_ventas": clientes_con_ventas,
        },
        "ingresos_por_vertical":     ingresos_por_vertical,
        "ciclo_venta_por_vertical":  ciclo_venta_por_vertical,
        "ciclo_venta_promedio_general_dias": ciclo_venta_promedio_general_dias,
        "dias_umbral_estancamiento": DIAS_ESTANCAMIENTO,
    }
