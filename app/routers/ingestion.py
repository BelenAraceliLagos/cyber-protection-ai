"""
router_ingestion.py — Endpoints para cargar y procesar documentos históricos.

Endpoints:
  POST /ingestion/upload     → sube archivos y extrae datos con IA
  POST /ingestion/confirm    → confirma y guarda cliente + servicios en BD
  POST /ingestion/save-logo  → guarda logo asociado a un cliente
"""

import os
import uuid
import shutil
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Query
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.client import Client
from app.models.service import Service
from app.services.extractor_service import procesar_archivo, guardar_logo

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])

# Directorio temporal para archivos subidos
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads_tmp")
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "assets")


# ── Schemas ───────────────────────────────────────────────────────────

class ClienteData(BaseModel):
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    email:        Optional[str] = None
    phone:        Optional[str] = None
    industry:     Optional[str] = None
    notes:        Optional[str] = None

class ServicioData(BaseModel):
    nombre:      str
    descripcion: Optional[str] = None
    precio_uf:   Optional[float] = None

class ConfirmRequest(BaseModel):
    cliente:           ClienteData
    servicios:         List[ServicioData] = []
    crear_servicios:   bool = True   # False = solo crear cliente
    logo_tmp_path:     Optional[str] = None  # path temporal del logo


# ── ENDPOINT 0: Verificar disponibilidad de Ollama ───────────────────

@router.get("/check-ollama")
def check_ollama(current_user: User = Depends(get_current_user)):
    """Verifica si Ollama está corriendo y el modelo disponible."""
    import requests as req
    try:
        r = req.get("http://localhost:11434/api/tags", timeout=5)
        if r.ok:
            modelos = [m["name"] for m in r.json().get("models", [])]
            gemma   = any("gemma" in m for m in modelos)
            return {
                "disponible": True,
                "modelos":    modelos,
                "gemma_listo": gemma,
                "mensaje":    "Ollama activo" if gemma else "Ollama activo pero sin modelo Gemma"
            }
    except Exception:
        pass
    return {
        "disponible":  False,
        "modelos":     [],
        "gemma_listo": False,
        "mensaje":     "Ollama no está corriendo. Ejecuta: ollama serve"
    }


# ── ENDPOINT 1: Subir y analizar archivos ─────────────────────────────

@router.post("/upload")
async def upload_and_extract(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Recibe uno o más archivos, extrae texto con IA y retorna
    los datos estructurados para que el usuario los revise.
    """
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    resultados = []

    # ── Verificar si hay documentos que necesitan Ollama ────────────
    EXTENSIONES_IMAGEN = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    hay_documentos = any(
        os.path.splitext(f.filename)[1].lower() not in EXTENSIONES_IMAGEN
        for f in files
    )

    if hay_documentos:
        import requests as req
        try:
            r_check = req.get("http://localhost:11434/api/tags", timeout=4)
            if not r_check.ok:
                raise HTTPException(status_code=503,
                    detail="Ollama no está disponible. Ejecuta 'ollama serve' en una terminal.")
            modelos = [m["name"] for m in r_check.json().get("models", [])]
            if not any("gemma" in m for m in modelos):
                raise HTTPException(status_code=503,
                    detail="Ollama activo pero sin modelo Gemma. Ejecuta: ollama pull gemma3:4b")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=503,
                detail="Ollama no está disponible. Ejecuta 'ollama serve' en una terminal.")

    for file in files:
        # Guardar archivo temporalmente
        ext       = file.filename.rsplit('.', 1)[-1] if '.' in file.filename else 'bin'
        tmp_name  = f"{uuid.uuid4().hex}.{ext}"
        tmp_path  = os.path.join(UPLOAD_DIR, tmp_name)

        with open(tmp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        try:
            resultado = procesar_archivo(
                ruta            = tmp_path,
                nombre_archivo  = file.filename,
                assets_dir      = ASSETS_DIR
            )
            resultado["tmp_path"] = tmp_path
            resultado["size_kb"]  = round(len(content) / 1024, 1)
            resultados.append(resultado)

        except RuntimeError as e:
            os.remove(tmp_path)
            raise HTTPException(status_code=503, detail=str(e))
        except Exception as e:
            os.remove(tmp_path)
            resultados.append({
                "nombre_archivo": file.filename,
                "error":          str(e),
                "datos":          None,
            })

    return {"archivos": resultados, "total": len(resultados)}


# ── ENDPOINT 2: Confirmar y guardar en BD ─────────────────────────────

@router.post("/confirm")
def confirm_and_save(
    request:      ConfirmRequest,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    """
    Recibe los datos revisados por el usuario y los guarda en la BD.
    - Crea o actualiza el cliente
    - Crea los servicios nuevos (si no existen ya)
    - Guarda el logo si se proporcionó
    """
    if not request.cliente.company_name:
        raise HTTPException(status_code=400, detail="El nombre de la empresa es obligatorio")

    # ── Cliente ──────────────────────────────────────────────────────
    # Verificar si ya existe
    cliente_existente = db.query(Client).filter(
        Client.company_name.ilike(f"%{request.cliente.company_name}%")
    ).first()

    if cliente_existente:
        # Actualizar campos vacíos con los nuevos datos
        for field in ['contact_name', 'email', 'phone', 'industry', 'notes']:
            val_actual = getattr(cliente_existente, field, None)
            val_nuevo  = getattr(request.cliente, field, None)
            if not val_actual and val_nuevo:
                setattr(cliente_existente, field, val_nuevo)
        db.commit()
        db.refresh(cliente_existente)
        cliente = cliente_existente
        accion_cliente = "actualizado"
    else:
        nuevo = Client(
            company_name = request.cliente.company_name,
            contact_name = request.cliente.contact_name or "Sin especificar",
            email        = request.cliente.email        or f"pendiente@{request.cliente.company_name.lower().replace(' ','')}.cl",
            phone        = request.cliente.phone,
            industry     = request.cliente.industry,
            notes        = request.cliente.notes,
        )
        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)
        cliente      = nuevo
        accion_cliente = "creado"

    # ── Logo ─────────────────────────────────────────────────────────
    logo_guardado = None
    if request.logo_tmp_path and os.path.exists(request.logo_tmp_path):
        logo_guardado = guardar_logo(
            ruta_origen     = request.logo_tmp_path,
            nombre_empresa  = request.cliente.company_name,
            assets_dir      = ASSETS_DIR
        )

    # ── Servicios ─────────────────────────────────────────────────────
    servicios_creados  = []
    servicios_existentes = []

    if request.crear_servicios:
        nombres_existentes = {
            s.name.lower().strip()
            for s in db.query(Service).all()
        }
        for srv_data in request.servicios:
            if not srv_data.nombre or not srv_data.nombre.strip():
                continue
            if srv_data.nombre.lower().strip() in nombres_existentes:
                servicios_existentes.append(srv_data.nombre)
                continue
            nuevo_srv = Service(
                name        = srv_data.nombre.strip(),
                description = srv_data.descripcion,
                base_price  = srv_data.precio_uf or 0.0,
                active      = True,
            )
            db.add(nuevo_srv)
            servicios_creados.append(srv_data.nombre)
            nombres_existentes.add(srv_data.nombre.lower().strip())

        db.commit()

    return {
        "ok":                   True,
        "cliente_id":           cliente.id,
        "cliente_nombre":       cliente.company_name,
        "accion_cliente":       accion_cliente,
        "logo_guardado":        logo_guardado,
        "servicios_creados":    servicios_creados,
        "servicios_existentes": servicios_existentes,
    }


# ── ENDPOINT 3: Guardar logo directamente como asset ─────────────────

class SaveLogoRequest(BaseModel):
    tmp_path:       str
    nombre_empresa: str

@router.post("/save-logo")
def save_logo_asset(
    req:          SaveLogoRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Guarda una imagen directamente en assets/ con nombre normalizado.
    No crea ni modifica ningún cliente en la BD.
    """
    import re
    from PIL import Image as PILImage

    # Intentar ruta tal como llega, luego como abspath
    ruta_original = req.tmp_path
    abs_path      = os.path.abspath(ruta_original)

    # Seguridad: verificar que el archivo existe y tiene extensión de imagen
    extensiones_ok = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    ext = os.path.splitext(abs_path)[1].lower()
    if ext not in extensiones_ok:
        raise HTTPException(status_code=400, detail="Solo se permiten imágenes")

    # Buscar el archivo — primero ruta original, luego abspath
    ruta_final = None
    for ruta in [ruta_original, abs_path]:
        if os.path.exists(ruta) and os.path.isfile(ruta):
            ruta_final = ruta
            break

    if not ruta_final:
        raise HTTPException(status_code=404,
            detail=f"Archivo no encontrado: {ruta_original}")

    # Normalizar nombre de empresa → nombre de archivo seguro
    nombre_norm = re.sub(r'[^a-z0-9\s]', '', req.nombre_empresa.lower())
    nombre_norm = re.sub(r'\s+', '_', nombre_norm).strip('_') or 'cliente'
    nombre_arch = f"logo_{nombre_norm}.jpg"
    ruta_dest   = os.path.join(ASSETS_DIR, nombre_arch)

    os.makedirs(ASSETS_DIR, exist_ok=True)
    try:
        img = PILImage.open(ruta_final).convert("RGB")
        img.save(ruta_dest, quality=95)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error guardando imagen: {e}")

    return {
        "ok":             True,
        "nombre_archivo": nombre_arch,
        "ruta":           ruta_dest,
        "mensaje":        f"Logo guardado como {nombre_arch}"
    }


# ── ENDPOINT 4: Preview de logo extraído ─────────────────────────────

@router.get("/logo-preview")
def logo_preview(path: str = Query(...)):
    """
    Sirve imágenes temporales para preview — sin auth para que el tag <img> pueda cargarlas.
    Solo acepta extensiones de imagen como seguridad mínima.
    """
    ext = os.path.splitext(path)[1].lower()
    if ext not in {'.jpg', '.jpeg', '.png', '.gif', '.webp'}:
        raise HTTPException(status_code=400, detail="Solo imágenes")

    # Buscar el archivo con ruta original y abspath
    ruta_final = None
    for ruta in [path, os.path.abspath(path)]:
        if os.path.exists(ruta) and os.path.isfile(ruta):
            ruta_final = ruta
            break

    if not ruta_final:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")

    media_type = {
        '.png':  'image/png',
        '.jpg':  'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif':  'image/gif',
        '.webp': 'image/webp',
    }.get(ext, 'image/jpeg')

    return FileResponse(ruta_final, media_type=media_type)


# ── ENDPOINT 4: Limpiar temporales ───────────────────────────────────

@router.delete("/cleanup")
def cleanup_tmp(current_user: User = Depends(get_current_user)):
    """Elimina archivos temporales de uploads."""
    try:
        if os.path.exists(UPLOAD_DIR):
            shutil.rmtree(UPLOAD_DIR)
            os.makedirs(UPLOAD_DIR, exist_ok=True)
        return {"ok": True, "mensaje": "Archivos temporales eliminados"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
