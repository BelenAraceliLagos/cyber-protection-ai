from sqlalchemy import Column, Integer, String, Text
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

    quotations = relationship(
        "Quotation",
        back_populates="client"
    )