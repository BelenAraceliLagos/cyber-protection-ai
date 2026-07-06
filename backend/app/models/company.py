from sqlalchemy import (
    JSON,
    Column,
    Integer,
    String,
    Boolean
)

from datetime import datetime

from app.core.database import Base


class Company(Base):

    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)

    name = Column(String, nullable=False)

    logo_path = Column(String)

    portada_path = Column(String)      # base portada
    interior_path = Column(String)     # base interior
    background_path = Column(String)   # foto de fondo

    primary_color   = Column(String)   # color texto portada
    secondary_color = Column(String)   # color fondo banner interior
    content_color   = Column(String)   # color texto contenido interior
    portada_config = Column(JSON, nullable=True, default=dict)

    active = Column(Boolean, default=True)

    # ── Condiciones comerciales (por empresa emisora) ───────────────
    rut = Column(String)
    direccion = Column(String)
    telefono = Column(String)

    notas_valores = Column(String)          # ej. "Los valores son netos y no incluyen IVA."
    formas_pago = Column(String)            # ej. "Contado, Transferencia Electrónica."
    modalidad_proyecto = Column(String)      # texto libre, párrafo completo
    modalidad_consultoria = Column(String)   # texto libre, párrafo completo

    banco = Column(String)                  # ej. "Banco Estado"
    datos_bancarios = Column(String)        # ej. "Chequera Electrónica Empresa N° ..."