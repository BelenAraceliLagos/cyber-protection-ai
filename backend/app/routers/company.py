"""
router/company.py — CRUD de empresas emisoras + upload de imágenes base.

Endpoints:
  GET    /companies/                    → lista todas
  GET    /companies/{id}                → detalle
  POST   /companies/                    → crear
  PUT    /companies/{id}                → editar
  DELETE /companies/{id}                → eliminar
  POST   /companies/{id}/upload-image   → sube base_portada | base_interior | logo
  GET    /companies/image-preview       → sirve imagen (público, solo assets/companies/)
"""

import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse as _FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user

from app.models.user import User
from app.models.company import Company

from app.schemas.company import (
    CompanyCreate,
    CompanyUpdate,
    CompanyResponse,
)

router = APIRouter(prefix="/companies", tags=["Companies"])

# ── Rutas base ─────────────────────────────────────────────────────────
_HERE      = Path(__file__).resolve().parent
ASSETS_DIR = (_HERE / ".." / ".." / "assets").resolve()
COMPANIES_DIR = ASSETS_DIR / "companies"


def _company_dir(company_id: int) -> Path:
    d = COMPANIES_DIR / f"company_{company_id}"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ── GET /companies/image-preview  (PÚBLICO — solo sirve assets/companies/) ──
@router.get("/image-preview")
def preview_image(path: str):
    """
    Sirve una imagen de plantilla almacenada en assets/companies/.
    Es público (sin auth) porque las imágenes de plantilla no son datos
    sensibles y los <img> del frontend no pueden enviar headers de auth.
    Validación de seguridad: solo permite rutas dentro de assets/companies/.
    """
    img_path = Path(path).resolve()

    # Validar que está dentro de assets/companies/ únicamente
    try:
        img_path.relative_to(COMPANIES_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    if not img_path.exists() or not img_path.is_file():
        raise HTTPException(status_code=404, detail="Imagen no encontrada")

    suffix = img_path.suffix.lower()
    media_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
    return _FileResponse(str(img_path), media_type=media_map.get(suffix, "image/png"))


# ── GET /companies/ ────────────────────────────────────────────────────
@router.get("/", response_model=list[CompanyResponse])
def get_companies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Company).order_by(Company.name.asc()).all()


# ── GET /companies/{id} ────────────────────────────────────────────────
@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


# ── POST /companies/ ───────────────────────────────────────────────────
@router.post("/", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
def create_company(
    data: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(Company).filter(Company.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe una empresa con ese nombre")

    company = Company(
        name=data.name,
        logo_path=data.logo_path,
        portada_path=data.portada_path,
        interior_path=data.interior_path,
        background_path=data.background_path,
        primary_color=data.primary_color,
        secondary_color=data.secondary_color,
        content_color=data.content_color,
        rut=data.rut,
        direccion=data.direccion,
        telefono=data.telefono,
        notas_valores=data.notas_valores,
        formas_pago=data.formas_pago,
        modalidad_proyecto=data.modalidad_proyecto,
        modalidad_consultoria=data.modalidad_consultoria,
        banco=data.banco,
        datos_bancarios=data.datos_bancarios,
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


# ── PUT /companies/{id} ────────────────────────────────────────────────
@router.put("/{company_id}", response_model=CompanyResponse)
def update_company(
    company_id: int,
    data: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    if data.name is not None:
        dup = db.query(Company).filter(
            Company.name == data.name, Company.id != company_id
        ).first()
        if dup:
            raise HTTPException(status_code=400, detail="Ya existe una empresa con ese nombre")
        company.name = data.name.strip()

    if data.logo_path is not None:
        company.logo_path = data.logo_path
    if data.background_path is not None:
        company.background_path = data.background_path
    if data.portada_path is not None:
        company.portada_path = data.portada_path
    if data.interior_path is not None:
        company.interior_path = data.interior_path
    if data.primary_color is not None:
        company.primary_color = data.primary_color
    if data.secondary_color is not None:
        company.secondary_color = data.secondary_color
    if data.content_color is not None:
        company.content_color = data.content_color
    if data.active is not None:
        company.active = data.active
    if data.portada_config is not None:
        company.portada_config = data.portada_config

    # Condiciones comerciales
    if data.rut is not None:
        company.rut = data.rut
    if data.direccion is not None:
        company.direccion = data.direccion
    if data.telefono is not None:
        company.telefono = data.telefono
    if data.notas_valores is not None:
        company.notas_valores = data.notas_valores
    if data.formas_pago is not None:
        company.formas_pago = data.formas_pago
    if data.modalidad_proyecto is not None:
        company.modalidad_proyecto = data.modalidad_proyecto
    if data.modalidad_consultoria is not None:
        company.modalidad_consultoria = data.modalidad_consultoria
    if data.banco is not None:
        company.banco = data.banco
    if data.datos_bancarios is not None:
        company.datos_bancarios = data.datos_bancarios

    db.commit()
    db.refresh(company)
    return company


# ── DELETE /companies/{id} ─────────────────────────────────────────────
@router.delete("/{company_id}")
def delete_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    db.delete(company)
    db.commit()
    return {"message": "Company deleted"}


# ── POST /companies/{id}/upload-image ──────────────────────────────────
@router.post("/{company_id}/upload-image", response_model=CompanyResponse)
async def upload_company_image(
    company_id: int,
    image_type: str = Form(...),   # "portada" | "interior" | "logo"
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Sube una imagen PNG/JPG para la empresa y actualiza la ruta en BD.
      portada  → base_portada.png  / portada_path
      interior → base_interior.png / interior_path
      logo     → logo.png          / logo_path
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    allowed = {"portada", "interior", "logo"}
    if image_type not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"image_type debe ser: {', '.join(allowed)}"
        )

    suffix = Path(file.filename).suffix.lower() if file.filename else ".png"
    if suffix not in {".png", ".jpg", ".jpeg"}:
        raise HTTPException(status_code=400, detail="Solo PNG o JPG")

    filename_map = {
        "portada":  f"base_portada{suffix}",
        "interior": f"base_interior{suffix}",
        "logo":     f"logo{suffix}",
    }
    dest_path = _company_dir(company_id) / filename_map[image_type]

    with dest_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    path_str = str(dest_path)
    if image_type == "portada":
        company.portada_path = path_str
    elif image_type == "interior":
        company.interior_path = path_str
    elif image_type == "logo":
        company.logo_path = path_str

    db.commit()
    db.refresh(company)
    return company
