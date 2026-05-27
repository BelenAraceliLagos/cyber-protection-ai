from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from app.core.database import get_db

from app.core.dependencies import get_current_user

from app.models.user import User
from app.models.client import Client
from app.models.service import Service
from app.models.quotation import Quotation
from app.models.quotation_item import QuotationItem

from app.schemas.quotation import (
    QuotationCreate,
    QuotationResponse
)

router = APIRouter(
    prefix="/quotations",
    tags=["Quotations"]
)

TAX_RATE = 0.19


@router.post(
    "/",
    response_model=QuotationResponse
)
def create_quotation(
    quotation_data: QuotationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    client = db.query(Client).filter(
        Client.id == quotation_data.client_id
    ).first()

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Client not found"
        )

    quotation = Quotation(
        client_id=quotation_data.client_id,
        created_by=current_user.id
    )

    db.add(quotation)

    subtotal = 0

    db.flush()

    for item in quotation_data.items:

        service = db.query(Service).filter(
            Service.id == item.service_id
        ).first()

        if not service:
            raise HTTPException(
                status_code=404,
                detail=f"Service {item.service_id} not found"
            )

        item_total = service.base_price * item.quantity

        subtotal += item_total

        quotation_item = QuotationItem(
            quotation_id=quotation.id,
            service_id=service.id,
            quantity=item.quantity,
            price=service.base_price
        )

        db.add(quotation_item)

    tax = subtotal * TAX_RATE

    total = subtotal + tax

    quotation.subtotal = subtotal
    quotation.tax = tax
    quotation.total = total

    db.commit()

    db.refresh(quotation)

    return quotation


@router.get(
    "/",
    response_model=list[QuotationResponse]
)
def get_quotations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return db.query(Quotation).all()


@router.get(
    "/{quotation_id}",
    response_model=QuotationResponse
)
def get_quotation(
    quotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    quotation = db.query(Quotation).filter(
        Quotation.id == quotation_id
    ).first()

    if not quotation:
        raise HTTPException(
            status_code=404,
            detail="Quotation not found"
        )

    return quotation