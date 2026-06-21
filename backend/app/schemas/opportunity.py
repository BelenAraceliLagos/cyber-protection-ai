from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class MilestoneCreate(BaseModel):
    tipo:         str = "reunion"
    titulo:       str
    descripcion:  str = ""
    completado:   bool = False
    fecha_inicio: Optional[datetime] = None
    fecha_fin:    Optional[datetime] = None


class MilestoneResponse(MilestoneCreate):
    id: int
    opportunity_id: int

    class Config:
        from_attributes = True


class OpportunityCreate(BaseModel):
    cliente_id:   int
    titulo:       str
    etapa:        str = "prospecto"
    probabilidad: int = 30
    valor_uf:     float = 0.0
    notas:        str = ""


class OpportunityPatch(BaseModel):
    titulo:       Optional[str]   = None
    etapa:        Optional[str]   = None
    probabilidad: Optional[int]   = None
    valor_uf:     Optional[float] = None
    notas:        Optional[str]   = None


class OpportunityResponse(OpportunityCreate):
    id:             int
    cliente_nombre: Optional[str] = None
    hitos:          List[MilestoneResponse] = []

    class Config:
        from_attributes = True
