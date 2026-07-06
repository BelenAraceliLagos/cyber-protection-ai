from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class CustomFontResponse(BaseModel):
    id: int
    name: str
    css_key: str
    has_regular: bool
    has_bold: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
