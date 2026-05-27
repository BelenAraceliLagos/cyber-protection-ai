from fastapi import FastAPI

from app.core.database import Base, engine

from app.models.user import User
from app.models.client import Client
from app.models.service import Service
from app.models.quotation import Quotation
from app.models.quotation_item import QuotationItem

from app.routers.client import router as client_router
from app.routers.auth import router as auth_router
from app.routers.service import router as service_router
from app.routers.quotation import router as quotation_router
from app.routers.ai import router as ai_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Cyber Protection AI",
    version="1.0.0"
)

app.include_router(client_router)
app.include_router(auth_router)
app.include_router(service_router)
app.include_router(quotation_router)
app.include_router(ai_router)

@app.get("/")
def root():
    return {
        "message": "Backend funcionando correctamente"
    }