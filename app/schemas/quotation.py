from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class QuotationItemCreate(BaseModel):
    service_id: int
    quantity: int = 1

class QuotationCreate(BaseModel):
    client_id: int
    items: List[QuotationItemCreate]

class QuotationItemResponse(BaseModel):
    id: int
    service_id: int
    quantity: int
    price: float

    class Config:
        from_attributes = True

class QuotationResponse(BaseModel):
    id: int
    client_id: int
    status: str
    subtotal: float
    tax: float
    total: float
    created_at: datetime

    items: List[QuotationItemResponse]

    class Config:
        from_attributes = True