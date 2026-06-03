"""
app/models/opportunity.py
Modelo de Oportunidades de Venta + Hitos (Gantt) + Notas de actividad.
"""

from sqlalchemy import (
    Column, Integer, String, Text, Float,
    DateTime, ForeignKey, Boolean, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class EtapaVenta(str, enum.Enum):
    prospecto   = "prospecto"
    propuesta   = "propuesta"
    negociacion = "negociacion"
    aprobacion  = "aprobacion"
    ganado      = "ganado"
    perdido     = "perdido"


class TipoHito(str, enum.Enum):
    reunion          = "reunion"
    entrega_propuesta = "entrega_propuesta"
    seguimiento      = "seguimiento"
    negociacion      = "negociacion"
    firma            = "firma"
    inicio_servicio  = "inicio_servicio"
    otro             = "otro"


class Opportunity(Base):
    __tablename__ = "opportunities"

    id              = Column(Integer, primary_key=True, index=True)
    cliente_id      = Column(Integer, ForeignKey("clients.id"), nullable=False)
    titulo          = Column(String, nullable=False)
    etapa           = Column(Enum(EtapaVenta), default=EtapaVenta.prospecto, nullable=False)
    probabilidad    = Column(Integer, default=30)          # 0-100 %
    valor_uf        = Column(Float, default=0.0)           # UF/mes estimadas
    industria       = Column(String)
    notas           = Column(Text)
    pdf_path        = Column(String)                       # ruta al último PDF generado
    service_ids_str = Column(String)                       # "1,3,7" — servicios vinculados
    creado_en       = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en  = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    cliente = relationship("Client", backref="opportunities")
    hitos   = relationship("Milestone", back_populates="opportunity",
                           cascade="all, delete-orphan", order_by="Milestone.fecha_inicio")
    notas_actividad = relationship("ActivityNote", back_populates="opportunity",
                                   cascade="all, delete-orphan", order_by="ActivityNote.creado_en.desc()")


class Milestone(Base):
    __tablename__ = "milestones"

    id              = Column(Integer, primary_key=True, index=True)
    opportunity_id  = Column(Integer, ForeignKey("opportunities.id"), nullable=False)
    tipo            = Column(Enum(TipoHito), nullable=False)
    titulo          = Column(String, nullable=False)
    descripcion     = Column(Text)
    fecha_inicio    = Column(DateTime(timezone=True))
    fecha_fin       = Column(DateTime(timezone=True))
    completado      = Column(Boolean, default=False)
    creado_en       = Column(DateTime(timezone=True), server_default=func.now())

    opportunity = relationship("Opportunity", back_populates="hitos")


class ActivityNote(Base):
    __tablename__ = "activity_notes"

    id             = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False)
    contenido      = Column(Text, nullable=False)
    autor          = Column(String)
    creado_en      = Column(DateTime(timezone=True), server_default=func.now())

    opportunity = relationship("Opportunity", back_populates="notas_actividad")
