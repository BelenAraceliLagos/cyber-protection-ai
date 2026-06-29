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
    active: bool

    class Config:
        from_attributes = True
