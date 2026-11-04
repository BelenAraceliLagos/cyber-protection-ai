from pydantic import BaseModel, Field
from typing import Optional

class ServiceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    base_price: float = Field(ge=0)
    active: bool = True

class ServiceResponse(ServiceCreate):
    id: int
    active: bool

    class Config:
        from_attributes = True