from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    ForeignKey,
    DateTime,
    Text
)

from sqlalchemy.orm import relationship

from datetime import datetime

from app.core.database import Base

class Quotation(Base):

    __tablename__ = "quotations"

    id = Column(Integer, primary_key=True, index=True)

    client_id = Column(
        Integer,
        ForeignKey("clients.id")
    )

    created_by = Column(
        Integer,
        ForeignKey("users.id")
    )

    status = Column(
        String,
        default="draft"
    )

    subtotal = Column(Float, default=0)

    tax = Column(Float, default=0)

    total = Column(Float, default=0)

    generated_text = Column(Text)

    pdf_path = Column(String)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    client = relationship(
        "Client",
        back_populates="quotations"
    )

    created_by_user = relationship(
        "User",
        back_populates="quotations"
    )

    items = relationship(
        "QuotationItem",
        back_populates="quotation",
        cascade="all, delete"
    )