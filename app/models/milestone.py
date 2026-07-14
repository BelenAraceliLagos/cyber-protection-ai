from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Milestone(Base):
    __tablename__ = "milestones"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False)
    tipo = Column(
        Enum(
            "reunion",
            "entrega_propuesta",
            "seguimiento",
            "negociacion",
            "firma",
            "inicio_servicio",
            "otro",
            name="tipohito",
        ),
        nullable=False,
    )
    titulo = Column(String, nullable=False)
    descripcion = Column(Text)
    fecha_inicio = Column(DateTime(timezone=True))
    fecha_fin = Column(DateTime(timezone=True))
    completado = Column(Boolean)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    opportunity = relationship("Opportunity", back_populates="milestones")
