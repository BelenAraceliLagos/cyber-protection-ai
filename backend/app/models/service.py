from sqlalchemy import Column, Integer, String, Float, Text, Boolean
from app.core.database import Base
from sqlalchemy.orm import relationship

class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    description = Column(Text)

    base_price = Column(Float, nullable=False)

    active = Column(Boolean, default=True)
    
    quotation_items = relationship(
    "QuotationItem",
    back_populates="service"
)