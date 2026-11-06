"""
textos_servicio_ia.py — Propone (NO guarda) los 3 textos de un servicio con IA.

Lo usa el botón "Generar con IA" del formulario de servicios. La persona
revisa/edita el texto y recién ahí lo guarda; desde ese momento el informe
lo usa tal cual, sin volver a llamar a la IA para ese texto.
"""

from app.services.ollama_service import _ollama, INSTRUCCION_TONO


def _contexto(nombre: str, descripcion: str, modalidad: str) -> str:
    return (
        f"Servicio: {nombre}\n"
        f"Modalidad: {modalidad or 'no indicada'}\n"
        f"Descripción base: {descripcion or 'no indicada'}\n"
    )


def proponer_textos_servicio(nombre: str, descripcion: str = "", modalidad: str = "") -> dict:
    """Devuelve {'texto_descripcion','texto_justificacion','texto_beneficio'}.
    Lanza RuntimeError (desde _ollama) si Ollama no está disponible."""
    ctx = _contexto(nombre, descripcion or "", modalidad or "")

    desc = _ollama(
        f"{INSTRUCCION_TONO}\n\n{ctx}\n"
        "Redacta un párrafo de 3 a 4 oraciones que describa qué incluye este "
        "servicio, para el informe que recibirá el cliente. No inventes normas "
        "ni cifras que no estén en la descripción base.",
        tokens=260,
    )
    just = _ollama(
        f"{INSTRUCCION_TONO}\n\n{ctx}\n"
        "Redacta un párrafo de 2 a 3 oraciones que justifique comercialmente por "
        "qué una empresa debería contratar este servicio.",
        tokens=200,
    )
    ben = _ollama(
        f"{INSTRUCCION_TONO}\n\n{ctx}\n"
        "Redacta UNA sola oración (máximo 25 palabras) con el beneficio "
        "estratégico principal de este servicio para el cliente.",
        tokens=80,
    )
    return {
        "texto_descripcion": desc.strip(),
        "texto_justificacion": just.strip(),
        "texto_beneficio": ben.strip(),
    }
