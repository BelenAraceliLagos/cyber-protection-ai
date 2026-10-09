from app.models.company import Company
from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from fastapi.responses import FileResponse

from app.services.pdf_service import (
    generate_quotation_pdf
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
    QuotationUpdate,
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
    company = db.query(Company).filter(
        Company.id == quotation_data.company_id
    ).first()

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found"
        )

    quotation = Quotation(
        client_id=quotation_data.client_id,
        company_id=quotation_data.company_id,
        created_by=current_user.id
    )

    db.add(quotation)

    subtotal = 0

    db.flush()

    for item in quotation_data.items:

        service = db.query(Service).filter(
            Service.id == item.service_id
        ).first()

        if not service.active:
            raise HTTPException(
                status_code=400,
                detail=f"Service {item.service_id} is inactive"
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

@router.post("/export-pdf/{quotation_id}")
def export_pdf(
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
    if not quotation.generated_text or not quotation.generated_text.strip():
        raise HTTPException(
            status_code=422,
            detail="La cotización no tiene texto generado por IA. Genera el texto antes de exportar el PDF."
        )

    pdf_path = generate_quotation_pdf(
        quotation
    )

    quotation.pdf_path = pdf_path

    db.commit()

    return FileResponse(
        path=pdf_path,
        filename=f"quotation_{quotation.id}.pdf",
        media_type="application/pdf"
    )
    
@router.put(
    "/{quotation_id}",
    response_model=QuotationResponse
)
def update_quotation(
    quotation_id: int,
    quotation_data: QuotationUpdate,
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

    if quotation_data.status is not None:
        quotation.status = quotation_data.status

    if quotation_data.generated_text is not None:
        quotation.generated_text = quotation_data.generated_text

    db.commit()
    db.refresh(quotation)

    return quotation

@router.delete(
    "/{quotation_id}"
)
def delete_quotation(
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

    db.delete(quotation)

    db.commit()

    return {
        "message": "Quotation deleted"
    }