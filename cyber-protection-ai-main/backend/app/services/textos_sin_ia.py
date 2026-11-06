"""
textos_sin_ia.py — Textos del informe cuando NO se usa IA (D-11).

Lógica pura (sin base de datos, sin Ollama): se puede probar sola.
Devuelve el mismo diccionario que ollama_service.generar_textos_completos(),
así el resto del generador de PDF no nota la diferencia.

Regla de prioridad por servicio (la aplica proposal.py):
  1) texto guardado en el servicio  ->  2) IA (si el modo es "Con IA")
  3) plantilla genérica de este módulo.
"""

from typing import List, Optional


def _lista_natural(items: List[str], maximo: int = 4) -> str:
    """['A','B','C'] -> 'A, B y C'. Si hay muchos: 'A, B, C, D y otros N servicios'."""
    items = [i for i in items if i]
    if not items:
        return "los servicios seleccionados"
    if len(items) > maximo:
        resto = len(items) - maximo
        return ", ".join(items[:maximo]) + f" y otros {resto} servicios"
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " y " + items[-1]


def justificacion_generica(nombre: str, empresa: str, industria: str) -> str:
    """Párrafo genérico para UN servicio, cuando no hay texto guardado."""
    return (
        f"{nombre} aporta a {empresa} una capacidad concreta para reducir su "
        f"exposición a riesgos de ciberseguridad en el sector {industria}, "
        f"con un alcance acotado, entregables definidos y seguimiento por parte "
        f"de nuestro equipo especializado."
    )


def construir_justificacion(servicios: List[dict], empresa: str, industria: str) -> str:
    """
    servicios: [{"nombre": str, "texto_justificacion": str|None}, ...]
    Un párrafo por servicio (separados por línea en blanco, como espera
    sec_justificacion()). Usa el texto guardado si existe; si no, el genérico.
    """
    parrafos = []
    for s in servicios:
        guardado = (s.get("texto_justificacion") or "").strip()
        if guardado:
            parrafos.append(f"{s['nombre']}: {guardado}")
        else:
            parrafos.append(justificacion_generica(s["nombre"], empresa, industria))
    return "\n\n".join(parrafos)


def generar_textos_plantilla(
    empresa_cliente: str,
    empresa_emisora: str,
    industria: str,
    servicios: List[str],
    antecedente: str = "",
    contacto: str = "",
    servicios_info: Optional[List[dict]] = None,
) -> dict:
    """Mismas claves que generar_textos_completos(), pero con texto fijo."""
    industria = industria or "tecnología"
    lista = _lista_natural(servicios)
    destinatario = contacto or "su equipo directivo"

    introduccion = (
        f"{empresa_emisora} presenta a {empresa_cliente} esta propuesta de servicios "
        f"de ciberseguridad, preparada para el sector {industria}. El documento "
        f"describe el alcance, la justificación y las condiciones comerciales de "
        f"{lista}, con el objetivo de fortalecer la postura de seguridad de su "
        f"organización y apoyar la continuidad de su operación."
    )

    alcance_intro = (
        f"Las organizaciones del sector {industria} enfrentan amenazas crecientes: "
        f"ransomware, fraude por ingeniería social, accesos indebidos y exigencias "
        f"regulatorias cada vez más estrictas. Los servicios propuestos para "
        f"{empresa_cliente} buscan identificar y reducir esos riesgos de forma "
        f"priorizada, comenzando por los de mayor impacto para el negocio."
    )

    valor_estrategico = (
        f"La implementación de {lista} permite a {empresa_cliente} anticipar "
        f"incidentes, responder con rapidez cuando ocurren y demostrar diligencia "
        f"ante clientes, reguladores y directorio. El resultado es menor riesgo "
        f"operacional, mayor confianza de sus partes interesadas y decisiones de "
        f"inversión en seguridad basadas en información concreta."
    )

    cierre_intro = (
        f"Agradecemos la oportunidad de presentar esta propuesta a {destinatario}. "
        f"{empresa_emisora} queda disponible para una reunión de alcance donde "
        f"se ajusten los servicios, plazos y valores a las necesidades específicas "
        f"de {empresa_cliente}."
    )

    frase_clave = (
        f"Seguridad que sostiene la continuidad de {empresa_cliente}."
    )

    if servicios_info:
        justificacion = construir_justificacion(servicios_info, empresa_cliente, industria)
    else:
        justificacion = "\n\n".join(
            justificacion_generica(n, empresa_cliente, industria) for n in servicios
        )

    return {
        "introduccion":            introduccion,
        "frase_clave":             frase_clave,
        "alcance_intro":           alcance_intro,
        "valor_estrategico":       valor_estrategico,
        "cierre_intro":            cierre_intro,
        "justificacion_servicios": justificacion,
        "antecedente_titulo":      "Antecedente del Cliente" if antecedente else None,
        "antecedente_descripcion": antecedente or "",
        "antecedente_bullets":     [],
    }
