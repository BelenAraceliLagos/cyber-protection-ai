"""
api/webhooks.py - ESTADO: NO ACTIVO, A PROPOSITO (decision D-06, hallazgo H-A04).

Recibe prospectos (leads) desde el sitio web y los crea como clientes.
NO esta registrado en main.py porque, tal como esta, cualquiera que conozca
la URL podria crear clientes: la validacion de la clave secreta (x_api_key)
esta comentada.

Requisitos ANTES de activarlo:
  1. Exigir una clave secreta leida desde el .env (por ejemplo WEBHOOK_API_KEY)
     y rechazar con 401 si falta o no coincide.
  2. Registrar el router en main.py y probar con la web real.
  3. Limitar la frecuencia de llamadas (evitar spam de clientes falsos).
Ver decisiones.md, D-06.
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.client import Client
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/webhooks", tags=["Webhooks Web"])

# Esquema de los datos que envía la página web
class WebLeadSchema(BaseModel):
    company_name: str
    contact_name: str
    email: EmailStr
    phone: str | None = None
    mensaje: str | None = None
    origen: str = "sitio_web"  # Canal de entrada

@router.post("/nuevo-lead")
def capturar_lead_web(
    lead: WebLeadSchema, 
    db: Session = Depends(get_db),
    x_api_key: str = Header(None)  # Seguridad opcional con Token Secreto
):
    # Opcional: Validar una clave secreta enviada desde la web
    # if x_api_key != "TU_CLAVE_SECRETA_SITIO_WEB":
    #     raise HTTPException(status_code=401, detail="No autorizado")

    # 1. Verificar si el cliente ya existe por su email
    cliente_existente = db.query(Client).filter(Client.email == lead.email).first()
    
    if cliente_existente:
        return {"mensaje": "El cliente ya existía en el CRM", "client_id": cliente_existente.id}

    # 2. Registrar el nuevo prospecto desde la web
    nuevo_cliente = Client(
        company_name=lead.company_name,
        contact_name=lead.contact_name,
        email=lead.email,
        phone=lead.phone,
        origen=lead.origen,
        lifecycle_stage="lead"  # Entra directo como Lead
    )
    
    db.add(nuevo_cliente)
    db.commit()
    db.refresh(nuevo_cliente)

    return {
        "status": "success", 
        "mensaje": "Lead registrado exitosamente en el CRM local", 
        "client_id": nuevo_cliente.id
    }