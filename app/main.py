from fastapi import FastAPI

from app.core.database import Base, engine

from app.models.user import User
from app.models.client import Client
from app.models.service import Service
from app.routers.auth import router as auth_router

from app.routers.client import router as client_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Cyber Protection AI",
    version="1.0.0"
)

app.include_router(client_router)
app.include_router(auth_router)

@app.get("/")
def root():
    return {
        "message": "Backend funcionando correctamente"
    }