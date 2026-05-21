from sqlalchemy import Column, Integer, String, Text
from app.core.database import Base

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)

    company_name = Column(String, nullable=False)

    contact_name = Column(String, nullable=False)

    email = Column(String, nullable=False)

    phone = Column(String)

    industry = Column(String)

    notes = Column(Text)