from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, func
from app.core.database import Base
from sqlalchemy.orm import relationship

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)

    company_name = Column(String, nullable=False)

    rut = Column(String, unique=True, index=True)

    business_name = Column(String)

    address = Column(String)

    city = Column(String)

    region = Column(String)

    country = Column(String, default="Chile")

    website = Column(String)

    contact_name = Column(String, nullable=False)

    email = Column(String, nullable=False)

    phone = Column(String)

    contact_position = Column(String)

    contact_phone = Column(String)

    industry = Column(String)

    notes = Column(Text)

    # ── CRM ──────────────────────────────────────────────────────────
    lifecycle_stage = Column(String, default="lead")   # lead|oportunidad|cliente|promotor
    lifecycle_auto  = Column(Boolean, default=True)     # si True, el sistema puede actualizar la etapa solo
    origen          = Column(String, nullable=True)    # referido|busqueda_organica|redes_sociales|email_marketing|trafico_directo|evento|otro
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    quotations = relationship(
        "Quotation",
        back_populates="client"
    )