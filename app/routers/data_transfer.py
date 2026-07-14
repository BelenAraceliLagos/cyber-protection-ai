"""
router/data_transfer.py — Export / Import de datos por módulo.

Objetivo: permitir sincronizar información entre entornos (ej. Gs <-> Andrés)
sin depender de dumps SQL crudos ni de Alembic para mover datos.

Diseño clave: el emparejamiento para evitar duplicados NO se hace por el id
numérico (que puede chocar entre dos bases distintas), sino por una
"clave natural" de cada tabla:

    clients      -> rut (o email si no hay rut)
    companies    -> name
    services     -> name
    users        -> email
    opportunities -> sin clave natural confiable: se resuelven sus datos
                     referenciados (cliente) por clave natural, y se
                     evita duplicar comparando (cliente_id resuelto, titulo)
    quotations   -> se tratan como históricas: siempre se insertan, pero
                     resolviendo client/company/user por clave natural y
                     cada item por el nombre del servicio

Endpoints:
    GET  /data-transfer/export                 -> JSON con todo
    POST /data-transfer/import                 -> importa JSON con todo
    GET  /data-transfer/export/{module}        -> JSON de un módulo
    POST /data-transfer/import/{module}        -> importa un módulo

Todos los endpoints requieren rol admin.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user

from app.models.user import User
from app.models.client import Client
from app.models.company import Company
from app.models.service import Service
from app.models.opportunity import Opportunity
from app.models.milestone import Milestone
from app.models.activity_note import ActivityNote
from app.models.quotation import Quotation
from app.models.quotation_item import QuotationItem

router = APIRouter(prefix="/data-transfer", tags=["Data Transfer"])

MODULES = [
    "companies",
    "services",
    "users",
    "clients",
    "opportunities",
    "quotations",
]


def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


def _dt(v):
    """Serializa datetimes a isoformat, deja el resto igual."""
    if isinstance(v, datetime):
        return v.isoformat()
    return v


def _parse_dt(v):
    if v is None:
        return None
    if isinstance(v, datetime):
        return v
    return datetime.fromisoformat(v)


# ── Export helpers por tabla ────────────────────────────────────────────

def _export_companies(db: Session) -> List[Dict[str, Any]]:
    out = []
    for c in db.query(Company).all():
        out.append({
            "name": c.name,
            "logo_path": c.logo_path,
            "portada_path": c.portada_path,
            "interior_path": c.interior_path,
            "background_path": c.background_path,
            "primary_color": c.primary_color,
            "secondary_color": c.secondary_color,
            "content_color": c.content_color,
            "portada_config": c.portada_config,
            "active": c.active,
        })
    return out


def _export_services(db: Session) -> List[Dict[str, Any]]:
    out = []
    for s in db.query(Service).all():
        out.append({
            "name": s.name,
            "description": s.description,
            "base_price": s.base_price,
            "active": s.active,
        })
    return out


def _export_users(db: Session) -> List[Dict[str, Any]]:
    out = []
    for u in db.query(User).all():
        out.append({
            "email": u.email,
            "name": u.name,
            "hashed_password": u.hashed_password,
            "role": u.role,
        })
    return out


def _export_clients(db: Session) -> List[Dict[str, Any]]:
    out = []
    for c in db.query(Client).all():
        out.append({
            "company_name": c.company_name,
            "contact_name": c.contact_name,
            "email": c.email,
            "phone": c.phone,
            "industry": c.industry,
            "notes": c.notes,
            "rut": c.rut,
            "business_name": c.business_name,
            "address": c.address,
            "city": c.city,
            "region": c.region,
            "country": c.country,
            "website": c.website,
            "contact_position": c.contact_position,
            "contact_phone": c.contact_phone,
        })
    return out


def _client_ref(client: Client) -> Dict[str, Any]:
    """Referencia natural a un cliente, para poder resolverlo en destino."""
    return {"rut": client.rut, "email": client.email, "company_name": client.company_name}


def _export_opportunities(db: Session) -> List[Dict[str, Any]]:
    out = []
    for o in db.query(Opportunity).all():
        out.append({
            "cliente_ref": _client_ref(o.client) if o.client else None,
            "titulo": o.titulo,
            "etapa": o.etapa,
            "probabilidad": o.probabilidad,
            "valor_uf": o.valor_uf,
            "notas": o.notas,
            "milestones": [{
                "tipo": m.tipo,
                "titulo": m.titulo,
                "descripcion": m.descripcion,
                "fecha_inicio": _dt(m.fecha_inicio),
                "fecha_fin": _dt(m.fecha_fin),
                "completado": m.completado,
            } for m in o.milestones],
            "activity_notes": [{
                "contenido": n.contenido,
                "autor": n.autor,
            } for n in o.activity_notes],
        })
    return out


def _export_quotations(db: Session) -> List[Dict[str, Any]]:
    out = []
    for q in db.query(Quotation).all():
        out.append({
            "cliente_ref": _client_ref(q.client) if q.client else None,
            "company_name": q.company.name if q.company else None,
            "created_by_email": q.created_by_user.email if q.created_by_user else None,
            "status": q.status,
            "subtotal": q.subtotal,
            "tax": q.tax,
            "total": q.total,
            "generated_text": q.generated_text,
            "pdf_path": q.pdf_path,
            "created_at": _dt(q.created_at),
            "items": [{
                "service_name": it.service.name if it.service else None,
                "quantity": it.quantity,
                "price": it.price,
            } for it in q.items],
        })
    return out


EXPORTERS = {
    "companies": _export_companies,
    "services": _export_services,
    "users": _export_users,
    "clients": _export_clients,
    "opportunities": _export_opportunities,
    "quotations": _export_quotations,
}


# ── Import helpers por tabla ─────────────────────────────────────────────
# Cada import devuelve un reporte {insertados, actualizados, omitidos, errores}

def _report():
    return {"insertados": 0, "actualizados": 0, "omitidos": 0, "errores": []}


def _import_companies(db: Session, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    rep = _report()
    for row in rows:
        try:
            existing = db.query(Company).filter(Company.name == row["name"]).first()
            if existing:
                for k, v in row.items():
                    setattr(existing, k, v)
                rep["actualizados"] += 1
            else:
                db.add(Company(**row))
                rep["insertados"] += 1
        except Exception as e:
            rep["errores"].append(f"{row.get('name')}: {e}")
    db.commit()
    return rep


def _import_services(db: Session, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    rep = _report()
    for row in rows:
        try:
            existing = db.query(Service).filter(Service.name == row["name"]).first()
            if existing:
                for k, v in row.items():
                    setattr(existing, k, v)
                rep["actualizados"] += 1
            else:
                db.add(Service(**row))
                rep["insertados"] += 1
        except Exception as e:
            rep["errores"].append(f"{row.get('name')}: {e}")
    db.commit()
    return rep


def _import_users(db: Session, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    rep = _report()
    for row in rows:
        try:
            existing = db.query(User).filter(User.email == row["email"]).first()
            if existing:
                for k, v in row.items():
                    setattr(existing, k, v)
                rep["actualizados"] += 1
            else:
                db.add(User(**row))
                rep["insertados"] += 1
        except Exception as e:
            rep["errores"].append(f"{row.get('email')}: {e}")
    db.commit()
    return rep


def _import_clients(db: Session, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    rep = _report()
    for row in rows:
        try:
            existing = None
            if row.get("rut"):
                existing = db.query(Client).filter(Client.rut == row["rut"]).first()
            if not existing and row.get("email"):
                existing = db.query(Client).filter(Client.email == row["email"]).first()
            if existing:
                for k, v in row.items():
                    setattr(existing, k, v)
                rep["actualizados"] += 1
            else:
                db.add(Client(**row))
                rep["insertados"] += 1
        except Exception as e:
            rep["errores"].append(f"{row.get('company_name')}: {e}")
    db.commit()
    return rep


def _resolve_client(db: Session, ref: Optional[Dict[str, Any]]) -> Optional[Client]:
    if not ref:
        return None
    if ref.get("rut"):
        c = db.query(Client).filter(Client.rut == ref["rut"]).first()
        if c:
            return c
    if ref.get("email"):
        c = db.query(Client).filter(Client.email == ref["email"]).first()
        if c:
            return c
    if ref.get("company_name"):
        c = db.query(Client).filter(Client.company_name == ref["company_name"]).first()
        if c:
            return c
    return None


def _import_opportunities(db: Session, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    rep = _report()
    for row in rows:
        try:
            client = _resolve_client(db, row.get("cliente_ref"))
            if not client:
                rep["omitidos"] += 1
                rep["errores"].append(f"{row.get('titulo')}: cliente no encontrado, importa clientes primero")
                continue

            existing = (
                db.query(Opportunity)
                .filter(Opportunity.cliente_id == client.id, Opportunity.titulo == row["titulo"])
                .first()
            )
            if existing:
                existing.etapa = row.get("etapa", existing.etapa)
                existing.probabilidad = row.get("probabilidad", existing.probabilidad)
                existing.valor_uf = row.get("valor_uf", existing.valor_uf)
                existing.notas = row.get("notas", existing.notas)
                opp = existing
                # sincroniza hijos: reemplaza por completo
                db.query(Milestone).filter(Milestone.opportunity_id == opp.id).delete()
                db.query(ActivityNote).filter(ActivityNote.opportunity_id == opp.id).delete()
                rep["actualizados"] += 1
            else:
                opp = Opportunity(
                    cliente_id=client.id,
                    titulo=row["titulo"],
                    etapa=row.get("etapa", "prospecto"),
                    probabilidad=row.get("probabilidad", 30),
                    valor_uf=row.get("valor_uf", 0.0),
                    notas=row.get("notas", ""),
                )
                db.add(opp)
                db.flush()  # para obtener opp.id
                rep["insertados"] += 1

            for m in row.get("milestones", []) or []:
                db.add(Milestone(
                    opportunity_id=opp.id,
                    tipo=m.get("tipo", "otro"),
                    titulo=m["titulo"],
                    descripcion=m.get("descripcion"),
                    fecha_inicio=_parse_dt(m.get("fecha_inicio")),
                    fecha_fin=_parse_dt(m.get("fecha_fin")),
                    completado=m.get("completado", False),
                ))
            for n in row.get("activity_notes", []) or []:
                db.add(ActivityNote(
                    opportunity_id=opp.id,
                    contenido=n["contenido"],
                    autor=n.get("autor"),
                ))
        except Exception as e:
            rep["errores"].append(f"{row.get('titulo')}: {e}")
    db.commit()
    return rep


def _import_quotations(db: Session, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    rep = _report()
    for row in rows:
        try:
            client = _resolve_client(db, row.get("cliente_ref"))
            if not client:
                rep["omitidos"] += 1
                rep["errores"].append("cotización omitida: cliente no encontrado")
                continue

            company = None
            if row.get("company_name"):
                company = db.query(Company).filter(Company.name == row["company_name"]).first()

            user = None
            if row.get("created_by_email"):
                user = db.query(User).filter(User.email == row["created_by_email"]).first()

            quotation = Quotation(
                client_id=client.id,
                company_id=company.id if company else None,
                created_by=user.id if user else None,
                status=row.get("status", "draft"),
                subtotal=row.get("subtotal", 0),
                tax=row.get("tax", 0),
                total=row.get("total", 0),
                generated_text=row.get("generated_text"),
                pdf_path=row.get("pdf_path"),
                created_at=_parse_dt(row.get("created_at")) or datetime.utcnow(),
            )
            db.add(quotation)
            db.flush()

            for it in row.get("items", []) or []:
                service = None
                if it.get("service_name"):
                    service = db.query(Service).filter(Service.name == it["service_name"]).first()
                if not service:
                    rep["errores"].append(f"item omitido: servicio '{it.get('service_name')}' no encontrado")
                    continue
                db.add(QuotationItem(
                    quotation_id=quotation.id,
                    service_id=service.id,
                    quantity=it.get("quantity", 1),
                    price=it.get("price"),
                ))
            rep["insertados"] += 1
        except Exception as e:
            rep["errores"].append(str(e))
    db.commit()
    return rep


IMPORTERS = {
    "companies": _import_companies,
    "services": _import_services,
    "users": _import_users,
    "clients": _import_clients,
    "opportunities": _import_opportunities,
    "quotations": _import_quotations,
}

# Orden seguro para respetar dependencias (FKs)
IMPORT_ORDER = ["companies", "services", "users", "clients", "opportunities", "quotations"]


# ── Endpoints ─────────────────────────────────────────────────────────────

@router.get("/export/{module}")
def export_module(module: str, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    if module not in EXPORTERS:
        raise HTTPException(status_code=404, detail=f"Módulo desconocido. Usa uno de: {MODULES}")
    return {module: EXPORTERS[module](db)}


@router.get("/export")
def export_all(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return {m: EXPORTERS[m](db) for m in IMPORT_ORDER}


@router.post("/import/{module}")
def import_module(
    module: str,
    payload: Dict[str, List[Dict[str, Any]]],
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    if module not in IMPORTERS:
        raise HTTPException(status_code=404, detail=f"Módulo desconocido. Usa uno de: {MODULES}")
    rows = payload.get(module, payload if isinstance(payload, list) else [])
    return {module: IMPORTERS[module](db, rows)}


@router.post("/import")
def import_all(
    payload: Dict[str, List[Dict[str, Any]]],
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    results = {}
    for module in IMPORT_ORDER:
        rows = payload.get(module, [])
        if rows:
            results[module] = IMPORTERS[module](db, rows)
    return results
