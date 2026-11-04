from sqlalchemy import Column, Integer, String
from app.core.database import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    email = Column(String, unique=True, nullable=False)

    hashed_password = Column(String, nullable=False)

    # ÚNICA fuente de autorización (H-A21): "admin" o "user".
    # Todo permiso del sistema se decide con este campo.
    role = Column(String, default="user")
    
    quotations = relationship(
    "Quotation",
    back_populates="created_by_user"
)
    profile = relationship("Profile", back_populates="user", cascade="all, delete-orphan")
    
    # RESIDUAL (H-A21): Role/UserRole existen en la base de datos pero NO gobiernan
    # permisos. El rol real es users.role. Integrarlas o eliminarlas: decisión pendiente con Andrés.
    role_links = relationship("UserRole", back_populates="user")