from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class CustomFont(Base):
    """
    Fuente personalizada subida por el usuario (no viene instalada en Windows
    por defecto), usada en el Editor de diseño y en la generación del PDF.

    Los archivos .ttf reales viven en disco (backend/assets/fonts/custom/),
    esta tabla solo guarda las rutas y metadatos.
    """
    __tablename__ = "custom_fonts"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)      # ej. "Montserrat"
    css_key = Column(String, nullable=False, unique=True)     # ej. "montserrat" (slug, usado en FONT_STACKS)
    regular_path = Column(String, nullable=True)              # ruta relativa al .ttf Regular
    bold_path = Column(String, nullable=True)                 # ruta relativa al .ttf Negrita
    created_at = Column(DateTime(timezone=True), server_default=func.now())
