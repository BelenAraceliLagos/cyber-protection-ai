from pydantic import BaseModel
from typing import Optional

class ClientCreate(BaseModel):
    company_name: str
    contact_name: str
    email: str
    phone: Optional[str] = None
    industry: Optional[str] = None
    notes: Optional[str] = None

class ClientResponse(ClientCreate):
    id: int

    class Config:
        from_attributes = True
        
class ClientUpdate(BaseModel):
    company_name: str
    contact_name: str
    email: str
    phone: Optional[str] = None
    industry: Optional[str] = None
    notes: Optional[str] = None