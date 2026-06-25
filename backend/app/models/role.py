from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String)

    user_links = relationship(
        "UserRole",
        back_populates="role",
    )
    
    role_links = relationship("UserRole", back_populates="role", overlaps="user_links")
