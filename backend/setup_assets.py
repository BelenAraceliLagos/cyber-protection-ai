"""
setup_assets.py — Convierte pdf_base.pdf a las imágenes base del template.
Ejecutar UNA SOLA VEZ desde la carpeta backend/ con el venv activado:

    python setup_assets.py

Requiere: pdf2image + poppler instalados.
  Windows: https://github.com/oschwartz10612/poppler-windows/releases
  Copiar bin/ de poppler al PATH o indicar la ruta en poppler_path=
"""

from pathlib import Path
from pdf2image import convert_from_path

BASE_DIR   = Path(__file__).parent
ASSETS_DIR = BASE_DIR.parent / "assets"
PDF_BASE   = ASSETS_DIR / "pdf_base.pdf"

def main():
    if not PDF_BASE.exists():
        print(f"[ERROR] No se encontró: {PDF_BASE}")
        print("  → Copia pdf_base.pdf a la carpeta assets/ del proyecto.")
        return

    print(f"Convirtiendo {PDF_BASE} a PNG a 300 DPI...")

    # En Windows, si poppler no está en PATH, especifica poppler_path:
    # pages = convert_from_path(str(PDF_BASE), dpi=300, poppler_path=r"C:\poppler\bin")
    pages = convert_from_path(str(PDF_BASE), dpi=300)

    if len(pages) < 2:
        print(f"[ERROR] Se esperaban 2 páginas, se encontraron {len(pages)}.")
        return

    portada_path  = ASSETS_DIR / "base_portada.png"
    interior_path = ASSETS_DIR / "base_interior.png"

    pages[0].save(str(portada_path),  "PNG")
    pages[1].save(str(interior_path), "PNG")

    print(f"[OK] base_portada.png  → {portada_path}")
    print(f"[OK] base_interior.png → {interior_path}")
    print("\nListo. Ahora puedes generar propuestas con WeasyPrint.")

if __name__ == "__main__":
    main()
