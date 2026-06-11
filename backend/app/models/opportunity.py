from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    titulo = Column(String, nullable=False)
    etapa = Column(
        Enum(
            "prospecto",
            "propuesta",
            "negociacion",
            "aprobacion",
            "ganado",
            "perdido",
            name="etapaventa",
        ),
        nullable=False,
    )
    probabilidad = Column(Integer)
    valor_uf = Column(Float)
    industria = Column(String)
    notas = Column(Text)
    pdf_path = Column(String)
    service_ids_str = Column(String)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True))

    client = relationship("Client", back_populates="opportunities")
    milestones = relationship(
        "Milestone",
        back_populates="opportunity",
        cascade="all, delete-orphan",
    )
    activity_notes = relationship(
        "ActivityNote",
        back_populates="opportunity",
        cascade="all, delete-orphan",
    )
