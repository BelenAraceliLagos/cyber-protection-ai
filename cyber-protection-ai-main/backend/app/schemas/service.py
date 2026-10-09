from pydantic import BaseModel
from typing import Optional

class ServiceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    base_price: float
    active: bool = True

class ServiceResponse(ServiceCreate):
    id: int
    active: bool

    class Config:
        from_attributes = True