from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Role(Base):
    # RESIDUAL (H-A21): esta tabla NO gobierna permisos. El rol real es users.role.
    # Se conserva sin uso hasta decidir con Andrés si se integra o se elimina.
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String)

    user_links = relationship(
        "UserRole",
        back_populates="role",
    )

    
    role_links = relationship("UserRole", back_populates="role", overlaps="user_links")
