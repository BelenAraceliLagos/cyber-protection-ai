from sqlalchemy import (
    Column,
    Integer,
    Float,
    ForeignKey
)

from sqlalchemy.orm import relationship

from app.core.database import Base

class QuotationItem(Base):

    __tablename__ = "quotation_items"

    id = Column(Integer, primary_key=True, index=True)

    quotation_id = Column(
        Integer,
        ForeignKey("quotations.id")
    )

    service_id = Column(
        Integer,
        ForeignKey("services.id")
    )

    quantity = Column(Integer, default=1)

    price = Column(Float)

    quotation = relationship(
        "Quotation",
        back_populates="items"
    )

    service = relationship(
        "Service",
        back_populates="quotation_items"
    )