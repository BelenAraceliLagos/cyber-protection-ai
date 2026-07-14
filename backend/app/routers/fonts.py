"""
router/fonts.py — Fuentes personalizadas para el Editor de diseño y el PDF.

Endpoints:
    GET    /fonts                       → lista fuentes personalizadas (autenticado)
    POST   /fonts/upload                → sube Regular y/o Negrita (admin)
    DELETE /fonts/{id}                  → elimina una fuente (admin)
    GET    /fonts/{id}/file/{weight}     → sirve el archivo .ttf (público, solo lectura)

Al subir, si ya existe una fuente con el mismo nombre (comparando el slug),
se actualiza esa misma fila en vez de crear una duplicada — así puedes subir
primero el Regular y más tarde agregar la Negrita, y quedan en la misma fuente.
"""
import re
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.custom_font import CustomFont
from app.schemas.custom_font import CustomFontResponse

router = APIRouter(prefix="/fonts", tags=["Fonts"])

_HERE = Path(__file__).resolve().parent
ASSETS_DIR = (_HERE / ".." / ".." / "assets").resolve()
FONTS_DIR = ASSETS_DIR / "fonts" / "custom"
FONTS_DIR.mkdir(parents=True, exist_ok=True)


def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


def _slug(nombre: str) -> str:
    s = nombre.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s or "fuente"


def _to_response(f: CustomFont) -> CustomFontResponse:
    return CustomFontResponse(
        id=f.id,
        name=f.name,
        css_key=f.css_key,
        has_regular=bool(f.regular_path),
        has_bold=bool(f.bold_path),
        created_at=f.created_at,
    )


@router.get("", response_model=list[CustomFontResponse])
def list_fonts(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    fonts = db.query(CustomFont).order_by(CustomFont.name).all()
    return [_to_response(f) for f in fonts]


@router.post("/upload", response_model=CustomFontResponse)
async def upload_font(
    name: str = Form(...),
    regular: UploadFile | None = File(None),
    bold: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    if not regular and not bold:
        raise HTTPException(status_code=400, detail="Debes subir al menos un archivo (Regular o Negrita)")

    for f in (regular, bold):
        if f and f.filename and Path(f.filename).suffix.lower() not in {".ttf", ".otf"}:
            raise HTTPException(status_code=400, detail="Solo se aceptan archivos .ttf u .otf")

    key = _slug(name)
    existing = (
        db.query(CustomFont)
        .filter((CustomFont.css_key == key) | (CustomFont.name.ilike(name.strip())))
        .first()
    )

    font = existing or CustomFont(name=name.strip(), css_key=key)

    if regular:
        suffix = Path(regular.filename).suffix.lower()
        dest = FONTS_DIR / f"{key}_regular{suffix}"
        with dest.open("wb") as out:
            shutil.copyfileobj(regular.file, out)
        font.regular_path = str(dest)

    if bold:
        suffix = Path(bold.filename).suffix.lower()
        dest = FONTS_DIR / f"{key}_bold{suffix}"
        with dest.open("wb") as out:
            shutil.copyfileobj(bold.file, out)
        font.bold_path = str(dest)

    if not existing:
        db.add(font)
    db.commit()
    db.refresh(font)
    return _to_response(font)


@router.delete("/{font_id}")
def delete_font(font_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    font = db.query(CustomFont).filter(CustomFont.id == font_id).first()
    if not font:
        raise HTTPException(status_code=404, detail="Fuente no encontrada")
    for path_str in (font.regular_path, font.bold_path):
        if path_str:
            p = Path(path_str)
            if p.exists():
                p.unlink()
    db.delete(font)
    db.commit()
    return {"message": "Fuente eliminada"}


@router.get("/{font_id}/file/{weight}")
def get_font_file(font_id: int, weight: str, db: Session = Depends(get_db)):
    """Sirve el archivo .ttf/.otf real — usado por el <link>/@font-face del
    navegador en el editor para previsualizar la fuente en vivo."""
    if weight not in ("regular", "bold"):
        raise HTTPException(status_code=400, detail="weight debe ser 'regular' o 'bold'")

    font = db.query(CustomFont).filter(CustomFont.id == font_id).first()
    if not font:
        raise HTTPException(status_code=404, detail="Fuente no encontrada")

    path_str = font.regular_path if weight == "regular" else font.bold_path
    if not path_str:
        raise HTTPException(status_code=404, detail=f"Esta fuente no tiene versión {weight}")

    path = Path(path_str)
    # Seguridad: solo servir archivos dentro de assets/fonts/custom/
    if FONTS_DIR not in path.resolve().parents:
        raise HTTPException(status_code=403, detail="Ruta no permitida")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado en disco")

    media_type = "font/ttf" if path.suffix.lower() == ".ttf" else "font/otf"
    return FileResponse(path, media_type=media_type)
