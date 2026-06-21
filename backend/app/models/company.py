from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime
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

    primary_color = Column(String)
    secondary_color = Column(String)

    active = Column(Boolean, default=True)