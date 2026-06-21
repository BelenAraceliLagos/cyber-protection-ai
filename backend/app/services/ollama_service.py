"""
ollama_service.py — Generación de textos con IA local (Ollama/Gemma)

Tono: Español chileno, formal-ejecutivo, directo.
      Suficiente contexto técnico para que el cliente entienda el valor,
      sin ahondar en detalles de implementación.
"""

import requests
from typing import List

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL      = "gemma3:4b"

INSTRUCCION_TONO = """
Instrucciones de redacción (SIEMPRE respetar):
- Español chileno formal. Tratar a la empresa con "usted".
- Tono ejecutivo: directo, seguro, sin rodeos.
- No uses tecnicismos innecesarios. Si mencionas algo técnico, explícalo en una frase simple.
- Nada de viñetas, listas ni títulos dentro del texto.
- Sin frases genéricas como "en el mundo actual" o "en la era digital".
- Sin saludos, firmas ni meta-comentarios. Solo el texto pedido.
""".strip()


def _ollama(prompt: str, tokens: int = 300) -> str:
    """Llama a Ollama y retorna texto limpio."""
    try:
        r = requests.post(
            OLLAMA_URL,
            json={
                "model":  MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": tokens,
                    "temperature": 0.72,
                    "top_p": 0.9,
                }
            },
            timeout=300
        )
        r.raise_for_status()
        return r.json().get("response", "").strip()
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Ollama no está disponible. "
            "Ejecuta 'ollama serve' en otra terminal y vuelve a intentarlo."
        )
    except requests.exceptions.Timeout:
        raise RuntimeError("Ollama tardó demasiado. Reintenta o usa modo sin IA.")
    except Exception as e:
        raise RuntimeError(f"Error con Ollama: {e}")


def generar_introduccion(empresa, industria, servicios, antecedente=""):
    # Usar hasta 8 servicios para dar contexto real sin sobrecargar el prompt
    srvs = ", ".join(servicios[:8])
    n    = len(servicios)
    ctx  = f"Contexto importante del cliente: {antecedente}" if antecedente else ""
    prompt = f"""{INSTRUCCION_TONO}

Escribe el párrafo de introducción de una propuesta comercial de ciberseguridad.

Datos:
- Empresa cliente: {empresa}
- Industria: {industria}
- Cantidad de servicios propuestos: {n}
- Servicios principales: {srvs}
{ctx}

El párrafo debe:
- Presentar a Cyber-Protection como aliado estratégico especializado en {industria}
- Mencionar el contexto de amenazas específico de su industria en Chile
- Referirse brevemente a los servicios propuestos como un conjunto cohesionado
- Entre 100 y 140 palabras
- Comenzar directo con el texto, sin encabezado ni títulos

Solo escribe el párrafo."""
    return _ollama(prompt, 280)


def generar_analisis_riesgo(empresa, industria, antecedente=""):
    ctx = f"Antecedente específico del cliente: {antecedente}" if antecedente else ""
    prompt = f"""{INSTRUCCION_TONO}

Escribe un análisis de riesgo cibernético para la empresa "{empresa}" del sector "{industria}".
{ctx}

El texto debe:
- Describir los 3 riesgos más relevantes para su industria en Chile
- Para cada riesgo: nombrarlo y explicar en UNA frase por qué impacta a este tipo de empresa
- Mencionar alguna regulación chilena si aplica (Ley 21.459, Ley 19.628, etc.)
- Tono de alerta moderada: serio pero no alarmista
- Entre 120 y 160 palabras
- Sin títulos ni listas. Todo en párrafo corrido.

Solo escribe el análisis."""
    return _ollama(prompt, 320)


def generar_justificacion_servicios(empresa, industria, servicios):
    if len(servicios) <= 3:
        srvs = ", ".join(servicios)
    else:
        srvs = ", ".join(servicios[:-1]) + f" y {servicios[-1]}"
    prompt = f"""{INSTRUCCION_TONO}

Escribe la sección de justificación de servicios para una propuesta dirigida a "{empresa}" ({industria}).
Servicios propuestos: {srvs}

El texto debe:
- Explicar POR QUÉ estos servicios son los adecuados para este cliente
- Conectar cada grupo de servicios con un beneficio concreto para el negocio
- Usar lenguaje que entienda el gerente general, no solo el equipo de TI
- Entre 130 y 180 palabras
- Sin listas ni viñetas. Párrafo corrido.

Solo escribe la justificación."""
    return _ollama(prompt, 350)


def generar_valor_estrategico(empresa, industria, servicios):
    prompt = f"""{INSTRUCCION_TONO}

Escribe el párrafo de valor estratégico para convencer a "{empresa}" ({industria})
de implementar los {len(servicios)} servicios de ciberseguridad propuestos.

El texto debe:
- Hablar del retorno estratégico: reputación, continuidad operativa, confianza de clientes
- Mencionar que la ciberseguridad no es un gasto sino una ventaja competitiva
- Hacer referencia al costo de NO actuar (sin ser dramático)
- Sonar como un consejo de un asesor de confianza, no como una venta agresiva
- Entre 80 y 110 palabras

Solo escribe el párrafo."""
    return _ollama(prompt, 220)


def generar_conclusion(empresa, contacto, servicios):
    prompt = f"""{INSTRUCCION_TONO}

Escribe el párrafo de cierre de una propuesta de ciberseguridad para "{empresa}".
Contacto: {contacto}. Servicios propuestos: {len(servicios)}.

El texto debe:
- Agradecer la confianza y el tiempo dedicado a revisar la propuesta
- Invitar a una reunión de alcance para afinar detalles y costos
- Expresar disponibilidad y compromiso de Cyber-Protection
- Sonar cálido pero profesional
- Entre 60 y 90 palabras

Solo escribe el párrafo de cierre."""
    return _ollama(prompt, 180)


def generar_frase_clave(empresa, industria):
    prompt = f"""{INSTRUCCION_TONO}

Escribe UNA frase corta e impactante para destacar en una propuesta de ciberseguridad
para "{empresa}" del sector "{industria}".

La frase debe:
- Transmitir que proteger la organización es proteger su futuro
- Sonar memorable, no genérica
- Máximo 35 palabras
- Sin comillas

Solo escribe la frase."""
    return _ollama(prompt, 70)


def generar_textos_completos(
    empresa_cliente: str,
    industria: str,
    servicios: List[str],
    antecedente: str = "",
    contacto: str = ""
) -> dict:
    """
    Genera todas las secciones con IA en secuencia.
    servicios: lista de nombres de servicios tal como están en la BD.
    Retorna dict compatible con generar_propuesta().
    """
    print(f"\n🤖 Generando informe con Ollama (gemma3:4b) para: {empresa_cliente}")
    print(f"   Servicios ({len(servicios)}): {', '.join(servicios[:4])}{'...' if len(servicios) > 4 else ''}")

    print("  [1/6] Introducción...")
    introduccion = generar_introduccion(empresa_cliente, industria, servicios, antecedente)

    print("  [2/6] Análisis de riesgo / alcance...")
    analisis = generar_analisis_riesgo(empresa_cliente, industria, antecedente)

    print("  [3/6] Justificación de servicios...")
    justificacion = generar_justificacion_servicios(empresa_cliente, industria, servicios)

    print("  [4/6] Valor estratégico...")
    valor = generar_valor_estrategico(empresa_cliente, industria, servicios)

    print("  [5/6] Conclusión / cierre...")
    conclusion = generar_conclusion(empresa_cliente, contacto or "equipo directivo", servicios)

    print("  [6/6] Frase clave...")
    frase = generar_frase_clave(empresa_cliente, industria)

    print(f"  ✅ Textos generados correctamente\n")

    return {
        "introduccion":            introduccion,
        "frase_clave":             frase,
        "alcance_intro":           analisis,
        "valor_estrategico":       valor,
        "cierre_intro":            conclusion,
        "justificacion_servicios": justificacion,
        "antecedente_titulo":      "Antecedente del Cliente" if antecedente else None,
        "antecedente_descripcion": antecedente or "",
        "antecedente_bullets":     [],
    }

def generar_descripcion_servicio(nombre: str, descripcion_base: str, empresa: str, industria: str) -> dict:
    """
    Genera una descripción estructurada (JSON) para un servicio usando Ollama.
    Retorna dict con formato:
    {
        "intro": "...",
        "secciones": [
            {
                "titulo": "...",
                "items": [
                    {"label": "...", "subitems": ["...", "..."]}
                ]
            }
        ]
    }
    Si Ollama falla o el JSON es inválido, retorna la descripción base como texto plano.
    """
    import json

    prompt = f"""Eres un experto en ciberseguridad. Debes estructurar la descripción de un servicio para una propuesta comercial profesional.

Servicio: {nombre}
Empresa cliente: {empresa}
Industria: {industria}
Descripción base del servicio:
{descripcion_base}

Genera una descripción estructurada en formato JSON estricto. El JSON debe tener exactamente esta estructura:
{{
  "intro": "Párrafo introductorio del servicio, 2-3 oraciones, tono ejecutivo formal en español",
  "secciones": [
    {{
      "titulo": "Título de la sección (ej: Fases del Servicio, Actividades, Entregables)",
      "items": [
        {{
          "label": "Nombre del item o fase",
          "subitems": ["actividad o detalle 1", "actividad o detalle 2"]
        }}
      ]
    }}
  ]
}}

Reglas estrictas:
- Responde SOLO con el JSON, sin texto antes ni después, sin bloques de código, sin markdown
- El campo "intro" es obligatorio
- Mínimo 1 sección con mínimo 2 items
- Cada item debe tener entre 2 y 5 subitems
- Máximo 3 secciones
- Todo en español formal chileno
- Adaptar el contenido a la empresa {empresa} del sector {industria}"""

    try:
        raw = _ollama(prompt, tokens=1200)

        # Limpiar posibles bloques markdown que el modelo añada
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip().rstrip("```").strip()

        # Buscar el primer { y último } para extraer JSON válido
        inicio = raw.find("{")
        fin    = raw.rfind("}") + 1
        if inicio == -1 or fin == 0:
            raise ValueError("No se encontró JSON en la respuesta")

        data = json.loads(raw[inicio:fin])

        # Validar estructura mínima
        if "intro" not in data or "secciones" not in data:
            raise ValueError("JSON incompleto")
        if not isinstance(data["secciones"], list) or len(data["secciones"]) == 0:
            raise ValueError("Sin secciones")

        return data

    except Exception as e:
        print(f"  ⚠️  generar_descripcion_servicio falló para '{nombre}': {e}. Usando texto plano.")
        # Fallback: retornar None para que _srv_bloques use texto plano
        return None
