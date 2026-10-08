from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class ActivityNote(Base):
    __tablename__ = "activity_notes"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False)
    contenido = Column(Text, nullable=False)
    autor = Column(String)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    opportunity = relationship(
        "Opportunity",
        back_populates="activity_notes",
    )
