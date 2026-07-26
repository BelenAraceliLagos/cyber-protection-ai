from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Opportunity(Base):
    __tablename__ = "opportunities"

    id           = Column(Integer, primary_key=True, index=True)
    cliente_id   = Column(Integer, ForeignKey("clients.id"), nullable=False)
    company_id   = Column(Integer, ForeignKey("companies.id"), nullable=True)  # empresa emisora (marca)
    titulo       = Column(String, nullable=False)
    etapa        = Column(String, default="prospecto")   # prospecto|propuesta|negociacion|aprobacion|ganado|perdido
    probabilidad = Column(Integer, default=30)           # 0-100
    valor_uf     = Column(Float, default=0.0)          # valor MENSUAL en UF
    plazo_meses  = Column(Integer, nullable=True)       # 3|6|9|12 — plazo del contrato, si aplica
    notas        = Column(Text, default="")
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    client = relationship("Client", backref="opportunities")
    company = relationship("Company")
    milestones = relationship(
    "Milestone",
    back_populates="opportunity",
    cascade="all, delete-orphan"
)
    activity_notes = relationship(
        "ActivityNote",
        back_populates="opportunity",
        cascade="all, delete-orphan"
    )


