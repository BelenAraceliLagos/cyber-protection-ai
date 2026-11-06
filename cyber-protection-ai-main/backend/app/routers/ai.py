"""
routers/ai.py - ESTADO: NO ACTIVO (decision D-06, hallazgo H-A04).

Genera el texto de una cotizacion con IA (Ollama) y lo guarda en
quotations.generated_text. Funciona, pero NO esta registrado en main.py y
el frontend no lo llama: la generacion de propuestas con IA se hace hoy por
routers/proposal.py + services/generate_proposal.py.

Para activarlo: agregar en main.py
    from app.routers.ai import router as ai_router
    app.include_router(ai_router)
Antes de hacerlo, decidir con el equipo si reemplaza o complementa a
proposal.py (ver decisiones.md, D-06).
"""

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