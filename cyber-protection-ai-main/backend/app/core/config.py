from dotenv import load_dotenv
from pathlib import Path
import os

# Carpeta backend/ (dos niveles sobre app/core/config.py). Funciona igual en
# Windows, Linux y Docker (antes usaba una ruta con "\\" que solo servia en Windows).
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60)
)
