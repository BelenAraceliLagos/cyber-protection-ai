from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserRole(Base):
        # RESIDUAL (H-A21): esta tabla NO gobierna permisos. El rol real es users.role.
    # Se conserva sin uso hasta decidir con Andrés si se integra o se elimina.
    __tablename__ = "user_roles"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id"), primary_key=True)

    user = relationship("User", back_populates="role_links")
    role = relationship("Role", back_populates="user_links")
