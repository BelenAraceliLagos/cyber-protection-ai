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