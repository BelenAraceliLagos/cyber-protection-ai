from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.client import Client
from app.models.opportunity import Opportunity
from app.schemas.client import ClientCreate, ClientResponse
from app.core.dependencies import get_current_user

router = APIRouter(
    prefix="/clients",
    tags=["Clients"],
    dependencies=[Depends(get_current_user)]
)

@router.post("/", response_model=ClientResponse)
def create_client(
    client: ClientCreate,
    db: Session = Depends(get_db)
):
    new_client = Client(**client.model_dump())

    db.add(new_client)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ya existe un cliente con ese RUT")

    db.refresh(new_client)

    return new_client


@router.get("/", response_model=list[ClientResponse])
def get_clients(
    db: Session = Depends(get_db)
):
    return db.query(Client).all()

@router.get("/{client_id}", response_model=ClientResponse)
def get_client(
    client_id: int,
    db: Session = Depends(get_db)
):
    client = db.query(Client).filter(
        Client.id == client_id
    ).first()

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Client not found"
        )

    return client

@router.put("/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: int,
    client_data: ClientCreate,
    db: Session = Depends(get_db)
):
    client = db.query(Client).filter(
        Client.id == client_id
    ).first()

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Client not found"
        )

    for field, value in client_data.model_dump().items():
        setattr(client, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ya existe un cliente con ese RUT")

    db.refresh(client)

    return client

@router.delete("/{client_id}")
def delete_client(
    client_id: int,
    db: Session = Depends(get_db)
):
    client = db.query(Client).filter(
        Client.id == client_id
    ).first()

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Client not found"
        )

    oportunidades = db.query(Opportunity).filter(
        Opportunity.cliente_id == client_id
    ).all()

    if oportunidades:
        nombres = ", ".join(f'"{o.titulo}"' for o in oportunidades[:3])
        extra = f" y {len(oportunidades) - 3} mas" if len(oportunidades) > 3 else ""
        raise HTTPException(
            status_code=409,
            detail=(
                f"No se puede eliminar: este cliente tiene {len(oportunidades)} "
                f"oportunidad(es) asociada(s) ({nombres}{extra}). "
                f"Mueve o elimina esas oportunidades primero, o reasignalas a otro cliente."
            )
        )

    db.delete(client)
    db.commit()

    return {
        "message": "Client deleted"
    }