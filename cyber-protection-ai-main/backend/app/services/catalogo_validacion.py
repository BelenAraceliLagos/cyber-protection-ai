"""
services/catalogo_validacion.py - Revisa las filas leidas del Excel de catalogo
y decide que haria el sistema con cada una. NO guarda nada ni toca la base de
datos: recibe las filas del Excel y la lista de servicios actuales, y devuelve
un informe (la "vista previa").

Acciones posibles por fila:
    nuevo        -> se creara un servicio
    actualiza    -> se modificara un servicio existente
    sin_cambios  -> ya esta igual en la base, no se toca
    error        -> no se guardara (el motivo va en "errores")
"""

import math
import unicodedata

MODALIDADES_CONOCIDAS = [
    "Proyecto", "Recurrente Mensual", "Recurrente", "Taller One-Shot", "Taller",
    "Servicio On-demand", "Campaña Periódica", "Proyecto / Recurrente",
    "Proyecto / On-demand", "Proyecto + Servicio",
]

PRECIO_PROVISORIO = 100.0
AVISO_PRECIO = "RECORDAR MODIFICAR EL VALOR REAL DEL SERVICIO"

NOMBRE_MIN, NOMBRE_MAX = 3, 150
RESUMEN_MIN, RESUMEN_MAX = 10, 600
MODALIDAD_MAX = 60


def _norm(texto):
    """Minusculas, sin tildes y con espacios simples, para comparar nombres."""
    t = unicodedata.normalize("NFKD", str(texto or ""))
    t = "".join(c for c in t if not unicodedata.combining(c))
    return " ".join(t.lower().split())


def _leer_precio(valor):
    """Devuelve (numero, None) si sirve, o (None, motivo) si no."""
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        return None, "vacío"
    if isinstance(valor, bool):
        return None, "no es un número"
    if isinstance(valor, (int, float)):
        numero = float(valor)
    else:
        try:
            numero = float(str(valor).strip().replace(",", "."))
        except ValueError:
            return None, "no es un número"
    if not math.isfinite(numero):
        return None, "no es un número"
    if numero < 0:
        return None, "negativo"
    return numero, None


def _leer_activo(valor):
    """True / False, o None si no se entiende."""
    t = _norm(valor)
    if t in ("si", "true", "1", "activo", "yes"):
        return True
    if t in ("no", "false", "0", "inactivo"):
        return False
    return None


def _texto(valor):
    return None if valor is None else str(valor).strip()


def _armar_descripcion(resumen, detalle):
    """Resumen primero; si hay detalle ampliado, va despues, separado."""
    if detalle:
        return f"{resumen}\n\n{detalle}"
    return resumen


def _analizar_fila(f, por_nombre, vistos, ids_usados):
    errores, avisos = [], []

    # ---- campos de texto ----
    nombre = _texto(f.get("nombre"))
    if not nombre:
        errores.append("Falta el nombre del servicio.")
    elif not (NOMBRE_MIN <= len(nombre) <= NOMBRE_MAX):
        errores.append(f"El nombre debe tener entre {NOMBRE_MIN} y {NOMBRE_MAX} caracteres.")

    resumen = _texto(f.get("resumen"))
    if not resumen:
        errores.append("Falta la descripción resumen.")
    elif not (RESUMEN_MIN <= len(resumen) <= RESUMEN_MAX):
        errores.append(
            f"El resumen debe tener entre {RESUMEN_MIN} y {RESUMEN_MAX} caracteres "
            f"(tiene {len(resumen)}). El texto largo va en 'Detalle ampliado'."
        )

    modalidad = _texto(f.get("modalidad"))
    if not modalidad:
        errores.append("Falta la modalidad.")
    elif len(modalidad) > MODALIDAD_MAX:
        errores.append(f"La modalidad es demasiado larga (máx. {MODALIDAD_MAX} caracteres).")
    elif _norm(modalidad) not in {_norm(m) for m in MODALIDADES_CONOCIDAS}:
        avisos.append(f'Modalidad nueva: "{modalidad}" (no estaba en la lista conocida).')

    activo = _leer_activo(f.get("activo"))
    if activo is None:
        errores.append('La columna Activo debe decir "Sí" o "No".')

    detalle = _texto(f.get("detalle"))

    # ---- nombre repetido dentro del mismo archivo ----
    if nombre:
        clave = _norm(nombre)
        if clave in vistos:
            errores.append(f"El nombre está repetido (ya aparece en la fila {vistos[clave]}).")
        else:
            vistos[clave] = f["fila"]

    # ---- buscar el servicio que ya existe ----
    existente = None
    actual = _texto(f.get("nombre_actual"))
    if actual:
        existente = por_nombre.get(_norm(actual))
    if existente is None and nombre:
        existente = por_nombre.get(_norm(nombre))
    if actual and existente is None:
        avisos.append(
            f'No existe ningún servicio llamado "{actual}"; esta fila se tratará como servicio nuevo.'
        )

    if existente is not None:
        if existente["id"] in ids_usados:
            errores.append("Otra fila del archivo ya actualiza este mismo servicio.")
        else:
            ids_usados.add(existente["id"])
        # renombrar hacia un nombre que ya usa OTRO servicio
        otro = por_nombre.get(_norm(nombre)) if nombre else None
        if otro is not None and otro["id"] != existente["id"]:
            errores.append(f'Ya existe otro servicio llamado "{nombre}".')

    # ---- precio ----
    precio, motivo = _leer_precio(f.get("precio"))
    precio_corregido = False
    if precio is None:
        if existente is not None:
            precio = float(existente["base_price"])
            avisos.append(f"Precio {motivo}: se conserva el actual ({precio:g} UF).")
        else:
            precio = PRECIO_PROVISORIO
            precio_corregido = True
            avisos.append(f"Precio {motivo}: se usará {precio:g} UF. {AVISO_PRECIO}")

    resultado = {
        "fila": f["fila"],
        "nombre": nombre,
        "id": existente["id"] if existente else None,
        "avisos": avisos,
        "errores": errores,
        "precio_corregido": precio_corregido,
        "cambios": [],
        "datos": None,
    }

    if errores:
        resultado["accion"] = "error"
        return resultado

    datos = {
        "name": nombre,
        "description": _armar_descripcion(resumen, detalle),
        "modalidad": modalidad,
        "base_price": precio,
        "active": activo,
    }
    resultado["datos"] = datos

    if existente is None:
        resultado["accion"] = "nuevo"
        return resultado

    for campo, nuevo in datos.items():
        viejo = existente.get(campo)
        if campo == "base_price":
            distinto = abs(float(viejo or 0) - float(nuevo)) > 1e-9
        elif campo == "active":
            distinto = bool(viejo) != bool(nuevo)
        else:
            distinto = (viejo or "").strip() != (nuevo or "").strip()
        if distinto:
            resultado["cambios"].append(campo)

    resultado["accion"] = "actualiza" if resultado["cambios"] else "sin_cambios"
    return resultado


def analizar_catalogo(filas, existentes):
    """
    filas:      lista que devuelve leer_catalogo().
    existentes: servicios actuales, cada uno como diccionario con
                id, name, description, modalidad, base_price, active.
    Devuelve {"filas": [...], "resumen": {...}} sin guardar nada.
    """
    por_nombre = {_norm(e["name"]): e for e in existentes}
    vistos, ids_usados = {}, set()

    resultados = [_analizar_fila(f, por_nombre, vistos, ids_usados) for f in filas]

    resumen = {"nuevo": 0, "actualiza": 0, "sin_cambios": 0, "error": 0, "avisos": 0}
    for r in resultados:
        resumen[r["accion"]] += 1
        if r["avisos"]:
            resumen["avisos"] += 1
    resumen["total"] = len(resultados)
    resumen["se_puede_guardar"] = (resumen["nuevo"] + resumen["actualiza"]) > 0
    return {"filas": resultados, "resumen": resumen}
