from pydantic import BaseModel
from typing import Any, Dict, Optional


class CompanyCreate(BaseModel):
    name: str
    logo_path: str | None = None
    portada_path: str | None = None
    interior_path: str | None = None
    background_path: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
    content_color: str | None = None

    # Condiciones comerciales
    rut: str | None = None
    direccion: str | None = None
    telefono: str | None = None
    notas_valores: str | None = None
    formas_pago: str | None = None
    modalidad_proyecto: str | None = None
    modalidad_consultoria: str | None = None
    banco: str | None = None
    datos_bancarios: str | None = None


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    logo_path: Optional[str] = None
    background_path: Optional[str] = None
    portada_path: Optional[str] = None
    interior_path: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    content_color: Optional[str] = None
    portada_config: Optional[Dict[str, Any]] = None
    active: Optional[bool] = None

    # Condiciones comerciales
    rut: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    notas_valores: Optional[str] = None
    formas_pago: Optional[str] = None
    modalidad_proyecto: Optional[str] = None
    modalidad_consultoria: Optional[str] = None
    banco: Optional[str] = None
    datos_bancarios: Optional[str] = None


class CompanyResponse(BaseModel):
    id: int
    name: str
    logo_path: str | None
    portada_path: str | None
    interior_path: str | None
    background_path: str | None
    primary_color: str | None
    secondary_color: str | None
    content_color: str | None
    portada_config: Optional[Dict[str, Any]] = None
    active: bool

    # Condiciones comerciales
    rut: str | None = None
    direccion: str | None = None
    telefono: str | None = None
    notas_valores: str | None = None
    formas_pago: str | None = None
    modalidad_proyecto: str | None = None
    modalidad_consultoria: str | None = None
    banco: str | None = None
    datos_bancarios: str | None = None

    class Config:
        from_attributes = True
