from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import Base, engine, SessionLocal
from app.models.user import User, Profile, Role, UserRole
from app.models.client import Client
from app.models.service import Service
from app.models.opportunity import Opportunity, Milestone, ActivityNote

from app.routers.auth import router as auth_router
from app.routers.client import router as client_router
from app.routers.users import router as users_router
from app.routers.service import router as service_router
from app.routers.proposal import router as proposal_router
from app.routers.ingestion import router as ingestion_router
from app.routers.opportunities import router as opportunities_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Cyber Protection AI",
    version="2.1.0",
    description="Backend con gestión de usuarios, clientes, servicios, propuestas y pipeline de ventas"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(client_router)
app.include_router(service_router)
app.include_router(proposal_router)
app.include_router(ingestion_router)
app.include_router(opportunities_router)


@app.on_event("startup")
def seed_roles():
    db = SessionLocal()
    try:
        for name, desc in [
            ("admin", "Administrador del sistema"),
            ("user",  "Usuario comercial"),
        ]:
            if not db.query(Role).filter(Role.name == name).first():
                db.add(Role(name=name, description=desc))
        db.commit()
    finally:
        db.close()


@app.get("/")
def root():
    return {
        "mensaje": "Cyber Protection AI — Backend funcionando",
        "version": "2.1.0",
        "endpoints": {
            "autenticacion":  ["/auth/login", "/auth/me"],
            "usuarios":       ["/users/", "/users/{id}"],
            "clientes":       ["/clients/", "/clients/{id}"],
            "servicios":      ["/services/", "/services/{id}"],
            "propuestas":     ["/proposals/generate"],
            "oportunidades":  ["/opportunities/", "/opportunities/pipeline", "/opportunities/{id}/generate-pdf"],
            "documentacion":  "/docs",
        }
    }
