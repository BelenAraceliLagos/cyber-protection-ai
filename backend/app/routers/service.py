from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from app.core.database import get_db

from app.core.dependencies import get_current_user

from app.models.user import User
from app.models.service import Service

from app.schemas.service import (
    ServiceCreate,
    ServiceResponse
)

router = APIRouter(
    prefix="/services",
    tags=["Services"]
)

@router.post(
    "/",
    response_model=ServiceResponse
)
def create_service(
    service: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    new_service = Service(
        **service.model_dump()
    )

    db.add(new_service)

    db.commit()

    db.refresh(new_service)

    return new_service


@router.get(
    "/",
    response_model=list[ServiceResponse]
)
def get_services(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return db.query(Service).all()

@router.put(
    "/{service_id}",
    response_model=ServiceResponse
)
def update_service(
    service_id: int,
    service: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    db_service = db.query(Service).filter(
        Service.id == service_id
    ).first()

    if not db_service:
        raise HTTPException(
            status_code=404,
            detail="Service not found"
        )

    db_service.name = service.name
    db_service.description = service.description
    db_service.base_price = service.base_price

    db.commit()
    db.refresh(db_service)

    return db_service


@router.delete(
    "/{service_id}"
)
def delete_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    db_service = db.query(Service).filter(
        Service.id == service_id
    ).first()

    if not db_service:
        raise HTTPException(
            status_code=404,
            detail="Service not found"
        )

    db.delete(db_service)

    db.commit()

    return {
        "message": "Service deleted"
    }