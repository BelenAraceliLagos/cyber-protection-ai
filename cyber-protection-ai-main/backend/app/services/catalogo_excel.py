"""
services/catalogo_excel.py - Lee el Excel del catalogo de servicios.

Solo LEE el archivo y lo convierte en una lista de datos. No valida reglas
de negocio ni toca la base de datos: eso se hace en pasos siguientes.
"""

from io import BytesIO

from openpyxl import load_workbook

NOMBRE_HOJA = "Catalogo"

# Con que texto empieza cada encabezado -> nombre interno del campo.
# (Se compara solo el inicio, asi "Precio base (UF) *" y "Precio base" valen.)
COLUMNAS = {
    "nombre del servicio": "nombre",
    "nombre actual": "nombre_actual",
    "modalidad": "modalidad",
    "descripción resumen": "resumen",
    "detalle": "detalle",
    "precio": "precio",
    "activo": "activo",
}

# Columnas que tienen que existir en el archivo.
OBLIGATORIAS = ["nombre", "modalidad", "resumen", "precio", "activo"]


def _campo_de_encabezado(texto):
    """Devuelve el campo interno de un encabezado, o None si no lo conocemos."""
    limpio = str(texto or "").strip().lower()
    for inicio, campo in COLUMNAS.items():
        if limpio.startswith(inicio):
            return campo
    return None


def _limpiar(valor):
    """Texto sin espacios sobrantes; vacio se vuelve None."""
    if isinstance(valor, str):
        valor = valor.strip()
        return valor or None
    return valor


def leer_catalogo(contenido: bytes):
    """
    Recibe el archivo .xlsx (en bytes) y devuelve una lista de filas.
    Cada fila es un diccionario con 'fila' (numero real en Excel) y los campos.
    Si el archivo no sirve (sin hoja o sin columnas), lanza ValueError con un
    mensaje que se le puede mostrar al usuario.
    """
    try:
        libro = load_workbook(BytesIO(contenido), data_only=True, read_only=True)
    except Exception:
        raise ValueError("No se pudo abrir el archivo. ¿Es un Excel (.xlsx)?")

    if NOMBRE_HOJA not in libro.sheetnames:
        raise ValueError(f'El archivo no tiene una hoja llamada "{NOMBRE_HOJA}".')

    filas = libro[NOMBRE_HOJA].iter_rows(values_only=True)
    encabezados = next(filas, None)
    if not encabezados:
        raise ValueError("La hoja del catálogo está vacía.")

    # posicion de cada campo: {"nombre": 1, "modalidad": 3, ...}
    posicion = {}
    for i, texto in enumerate(encabezados):
        campo = _campo_de_encabezado(texto)
        if campo and campo not in posicion:
            posicion[campo] = i

    faltan = [c for c in OBLIGATORIAS if c not in posicion]
    if faltan:
        raise ValueError("Faltan columnas en el archivo: " + ", ".join(faltan))

    resultado = []
    for numero, fila in enumerate(filas, start=2):  # la fila 1 son los encabezados
        datos = {
            campo: _limpiar(fila[i]) if i < len(fila) else None
            for campo, i in posicion.items()
        }
        if all(v is None for v in datos.values()):
            continue  # fila totalmente vacia
        datos["fila"] = numero
        resultado.append(datos)

    return resultado
