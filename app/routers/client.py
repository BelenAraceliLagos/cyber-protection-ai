from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientResponse
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.client import ClientUpdate
from fastapi import HTTPException

router = APIRouter(
    prefix="/clients",
    tags=["Clients"]
)

@router.post("/", response_model=ClientResponse)
def create_client(
    client: ClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_client = Client(**client.model_dump())

    db.add(new_client)

    db.commit()

    db.refresh(new_client)

    return new_client


@router.get("/", response_model=list[ClientResponse])
def get_clients(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Client).all()

@router.put("/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: int,
    client_data: ClientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    client = db.query(Client).filter(
        Client.id == client_id
    ).first()

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Client not found"
        )

    for key, value in client_data.model_dump().items():
        setattr(client, key, value)

    db.commit()

    db.refresh(client)

    return client

@router.delete("/{client_id}")
def delete_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    client = db.query(Client).filter(
        Client.id == client_id
    ).first()

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Client not found"
        )

    db.delete(client)

    db.commit()

    return {
        "message": "Client deleted"
    }