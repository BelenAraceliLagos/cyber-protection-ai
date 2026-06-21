from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user

from app.models.user import User
from app.models.company import Company

from app.schemas.company import (
    CompanyCreate,
    CompanyUpdate,
    CompanyResponse
)

router = APIRouter(
    prefix="/companies",
    tags=["Companies"]
)


@router.get(
    "/",
    response_model=list[CompanyResponse]
)
def get_companies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Company).order_by(Company.name.asc()).all()


@router.get(
    "/{company_id}",
    response_model=CompanyResponse
)
def get_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    company = db.query(Company).filter(
        Company.id == company_id
    ).first()

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found"
        )

    return company


@router.post(
    "/",
    response_model=CompanyResponse,
    status_code=status.HTTP_201_CREATED
)
def create_company(
    data: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = db.query(Company).filter(
        Company.name == data.name
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Company already exists"
        )

    company = Company(
    name=data.name,

    logo_path=data.logo_path,
    portada_path=data.portada_path,
    interior_path=data.interior_path,
    background_path=data.background_path,

    primary_color=data.primary_color,
    secondary_color=data.secondary_color
    )

    db.add(company)

    db.commit()

    db.refresh(company)

    return company


@router.put(
    "/{company_id}",
    response_model=CompanyResponse
)
def update_company(
    company_id: int,
    data: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    company = db.query(Company).filter(
        Company.id == company_id
    ).first()

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found"
        )

    if data.name is not None:

        existing = db.query(Company).filter(
            Company.name == data.name,
            Company.id != company_id
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail="Company already exists"
            )

        company.name = data.name.strip()

    if data.logo_path is not None:
        company.logo_path = data.logo_path

    if data.background_path is not None:
        company.background_path = data.background_path
        
    if data.portada_path is not None:
        company.portada_path = data.portada_path
        
    if data.interior_path is not None:
        company.interior_path = data.interior_path

    if data.primary_color is not None:
        company.primary_color = data.primary_color

    if data.secondary_color is not None:
        company.secondary_color = data.secondary_color

    if data.active is not None:
        company.active = data.active

    db.commit()

    db.refresh(company)

    return company


@router.delete(
    "/{company_id}"
)
def delete_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    company = db.query(Company).filter(
        Company.id == company_id
    ).first()

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found"
        )

    db.delete(company)

    db.commit()

    return {
        "message": "Company deleted"
    }