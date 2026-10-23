from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class MilestoneCreate(BaseModel):
    tipo:         str = "reunion"
    titulo:       str
    descripcion:  str = ""
    completado:   bool = False
    importancia:  str = "Normal"
    fecha_inicio: Optional[datetime] = None
    fecha_fin:    Optional[datetime] = None


class MilestoneResponse(MilestoneCreate):
    id: int
    opportunity_id: int

    class Config:
        from_attributes = True


class OpportunityCreate(BaseModel):
    cliente_id:   int
    company_id:   Optional[int] = None   # empresa emisora (marca) — opcional
    titulo:       str
    etapa:        str = "prospecto"
    probabilidad: int = 30
    valor_uf:     float = 0.0
    plazo_meses:  Optional[int] = None
    notas:        str = ""
    probabilidad: int = Field(30, ge=0, le=100)


class OpportunityPatch(BaseModel):
    titulo:       Optional[str]   = None
    cliente_id:   Optional[int]   = None
    company_id:   Optional[int]   = None
    etapa:        Optional[str]   = None
    probabilidad: Optional[int]   = None
    valor_uf:     Optional[float] = None
    plazo_meses:  Optional[int]   = None
    notas:        Optional[str]   = None
    motivo_cierre:  Optional[str] = None
    detalle_cierre: Optional[str] = None
    probabilidad: Optional[int]   = Field(None, ge=0, le=100)


class OpportunityResponse(OpportunityCreate):
    id:             int
    cliente_nombre: Optional[str] = None
    company_nombre: Optional[str] = None
    closed_at:      Optional[datetime] = None
    motivo_cierre:  Optional[str] = None
    detalle_cierre: Optional[str] = None
    motivo_previo:  Optional[str] = None
    hitos:          List[MilestoneResponse] = []

    class Config:
        from_attributes = True
