from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base

class Opportunity(Base):
    __tablename__ = "opportunities"

    id           = Column(Integer, primary_key=True, index=True)
    cliente_id   = Column(Integer, ForeignKey("clients.id"), nullable=False)
    titulo       = Column(String, nullable=False)
    etapa        = Column(String, default="prospecto")   # prospecto|propuesta|negociacion|aprobacion|ganado|perdido
    probabilidad = Column(Integer, default=30)           # 0-100
    valor_uf     = Column(Float, default=0.0)
    notas        = Column(Text, default="")

    client = relationship("Client", backref="opportunities")
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


