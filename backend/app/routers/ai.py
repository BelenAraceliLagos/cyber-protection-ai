from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from app.core.database import get_db

from app.core.dependencies import get_current_user

from app.models.user import User
from app.models.quotation import Quotation

from app.services.prompt_service import (
    build_quotation_prompt
)

from app.services.ollama_service import (
    generate_text
)

router = APIRouter(
    prefix="/ai",
    tags=["AI"]
)

@router.post("/generate/{quotation_id}")
def generate_quotation_ai(
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

    prompt = build_quotation_prompt(
        quotation.client,
        quotation
    )

    generated_text = generate_text(prompt)

    quotation.generated_text = generated_text

    db.commit()

    return {
        "message": "AI content generated",
        "generated_text": generated_text
    }