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