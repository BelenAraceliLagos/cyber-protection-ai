from pydantic import BaseModel, field_validator
from typing import Optional


def clean_rut(value: str) -> str:
    return value.replace(".", "").replace("-", "").strip().upper()


def is_valid_chilean_rut(value: str) -> bool:
    rut = clean_rut(value)
    if len(rut) < 2 or not rut[:-1].isdigit():
        return False

    body = rut[:-1]
    check_digit = rut[-1]
    multiplier = 2
    total = 0

    for digit in reversed(body):
        total += int(digit) * multiplier
        multiplier = 2 if multiplier == 7 else multiplier + 1

    expected_value = 11 - (total % 11)
    expected = "0" if expected_value == 11 else "K" if expected_value == 10 else str(expected_value)
    return check_digit == expected


class ClientCreate(BaseModel):
    company_name: str
    rut: Optional[str] = None
    business_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = "Chile"
    website: Optional[str] = None
    contact_name: str
    email: str
    phone: Optional[str] = None
    contact_position: Optional[str] = None
    contact_phone: Optional[str] = None
    industry: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("rut")
    @classmethod
    def validate_rut(cls, value: Optional[str]) -> Optional[str]:
        if value is None or not value.strip():
            return None
        if not is_valid_chilean_rut(value):
            raise ValueError("RUT de empresa inválido")
        rut = clean_rut(value)
        return f"{rut[:-1]}-{rut[-1]}"

    @field_validator("country")
    @classmethod
    def default_country(cls, value: Optional[str]) -> str:
        return value.strip() if value and value.strip() else "Chile"


class ClientResponse(ClientCreate):
    id: int

    class Config:
        from_attributes = True
