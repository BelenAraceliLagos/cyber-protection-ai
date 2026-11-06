"""
routers/ingestion.py - Importacion de informacion externa (Excel, PDF, Word).

Por ahora contiene la importacion del CATALOGO DE SERVICIOS desde Excel, en
dos pasos separados:

    POST /ingestion/catalogo/preview    -> revisa el archivo y muestra que haria
                                           (NO guarda nada)
    POST /ingestion/catalogo/confirmar  -> vuelve a revisar el archivo y guarda
                                           solo las filas validas

Los dos reciben el mismo archivo .xlsx. El segundo lo revisa de nuevo por
seguridad, porque la base pudo cambiar entre una llamada y otra.
Solo para administradores.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.service import Service
from app.models.user import User
from app.routers.user import require_admin
from app.services.catalogo_excel import leer_catalogo
from app.services.catalogo_validacion import analizar_catalogo

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])

TAMANO_MAXIMO = 5 * 1024 * 1024  # 5 MB


def _leer_archivo(archivo: UploadFile) -> bytes:
    """Lee el archivo subido y revisa tipo y tamano."""
    nombre = (archivo.filename or "").lower()
    if not nombre.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="El archivo debe ser un Excel (.xlsx).")
    contenido = archivo.file.read(TAMANO_MAXIMO + 1)
    if len(contenido) > TAMANO_MAXIMO:
        raise HTTPException(status_code=413, detail="El archivo es demasiado grande (máx. 5 MB).")
    if not contenido:
        raise HTTPException(status_code=400, detail="El archivo está vacío.")
    return contenido


def _analizar(db: Session, archivo: UploadFile):
    """Lee el Excel, trae los servicios actuales y devuelve el informe."""
    contenido = _leer_archivo(archivo)
    try:
        filas = leer_catalogo(contenido)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not filas:
        raise HTTPException(status_code=400, detail="La hoja Catalogo no tiene filas con datos.")

    existentes = [
        {
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "modalidad": s.modalidad,
            "base_price": s.base_price,
            "active": s.active,
        }
        for s in db.query(Service).all()
    ]
    return analizar_catalogo(filas, existentes)


@router.post("/catalogo/preview")
def catalogo_preview(
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Muestra que haria la importacion. No guarda nada."""
    return _analizar(db, archivo)


@router.post("/catalogo/confirmar")
def catalogo_confirmar(
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Guarda las filas validas (nuevas y actualizadas). Las filas con error se omiten."""
    informe = _analizar(db, archivo)

    creados = actualizados = omitidos = 0
    try:
        for fila in informe["filas"]:
            accion = fila["accion"]
            if accion == "nuevo":
                db.add(Service(**fila["datos"]))
                creados += 1
            elif accion == "actualiza":
                servicio = db.query(Service).filter(Service.id == fila["id"]).first()
                if servicio is None:
                    omitidos += 1
                    continue
                for campo in fila["cambios"]:
                    setattr(servicio, campo, fila["datos"][campo])
                actualizados += 1
            else:
                omitidos += 1  # sin_cambios o error
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="No se pudo guardar. No se hizo ningún cambio.")

    return {
        "creados": creados,
        "actualizados": actualizados,
        "omitidos": omitidos,
        "resumen_previo": informe["resumen"],
    }
