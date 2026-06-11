from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean)
    name = Column(String, nullable=False)
    role = Column(String, server_default="user")

    profile = relationship(
        "Profile",
        back_populates="user",
        uselist=False,
    )
    role_links = relationship("UserRole", back_populates="user")
    quotations = relationship(
        "Quotation",
        back_populates="created_by_user",
    )
