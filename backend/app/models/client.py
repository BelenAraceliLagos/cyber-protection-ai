from sqlalchemy import Column, Index, Integer, String, Text, text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Client(Base):
    __tablename__ = "clients"
    __table_args__ = (
        Index(
            "ix_clients_rut",
            "rut",
            unique=True,
            postgresql_where=text("rut IS NOT NULL"),
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, nullable=False)
    contact_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String)
    industry = Column(String)
    notes = Column(Text)
    rut = Column(String)
    business_name = Column(String)
    address = Column(String)
    city = Column(String)
    region = Column(String)
    country = Column(String, server_default="Chile")
    website = Column(String)
    contact_position = Column(String)
    contact_phone = Column(String)

    opportunities = relationship("Opportunity", back_populates="client")
    quotations = relationship(
        "Quotation",
        back_populates="client",
    )
