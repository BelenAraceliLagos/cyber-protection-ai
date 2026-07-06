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
Eres un consultor senior de ciberseguridad redactando una propuesta comercial profesional.
Reglas OBLIGATORIAS — no negociables:
- Español formal chileno. Tratar siempre con "usted" y "su empresa/organización".
- Tono ejecutivo: concreto, seguro, orientado al negocio. Sin rodeos.
- PROHIBIDO: frases genéricas como "en el mundo actual", "en la era digital", "es fundamental destacar", "en conclusión", "en resumen".
- PROHIBIDO: viñetas, listas con guiones, títulos o subtítulos dentro del texto.
- PROHIBIDO: saludos, despedidas, firmas, comillas al inicio/final, ni comentarios sobre la tarea.
- PROHIBIDO: repetir el nombre de la empresa más de 2 veces en el mismo párrafo.
- Solo escribe el texto pedido. Nada más.
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
                    "temperature": 0.65,
                    "top_p": 0.88,
                    "repeat_penalty": 1.15,
                }
            },
            timeout=300
        )
        r.raise_for_status()
        text = r.json().get("response", "").strip()
        # Limpiar artefactos comunes del modelo
        for prefix in ['```', '**', '##', '# ']:
            if text.startswith(prefix):
                text = text.lstrip('#* `\n')
        return text
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Ollama no está disponible. "
            "Ejecuta 'ollama serve' en otra terminal y vuelve a intentarlo."
        )
    except requests.exceptions.Timeout:
        raise RuntimeError("Ollama tardó demasiado. Reintenta o usa modo sin IA.")
    except Exception as e:
        raise RuntimeError(f"Error con Ollama: {e}")


def generar_introduccion(
    empresa,
    empresa_emisora,
    industria,
    servicios,
    antecedente=""
):
    srvs = ", ".join(servicios[:6])
    n = len(servicios)

    ctx = (
        f"\nContexto específico del cliente (úsalo para personalizar):\n{antecedente}"
        if antecedente else ""
    )

    prompt = f"""{INSTRUCCION_TONO}

TAREA: Escribe el párrafo introductorio de una propuesta de ciberseguridad.

DATOS:
- Cliente: {empresa} (sector {industria})
- Empresa que emite la propuesta: {empresa_emisora}
- Servicios propuestos ({n}): {srvs}
{ctx}

ESTRUCTURA DEL PÁRRAFO (en este orden):
1. Primera oración: presentar a {empresa_emisora} como aliado estratégico especializado en ciberseguridad para el sector {industria}.
2. Segunda y tercera oración: describir el desafío específico de ciberseguridad que enfrenta {empresa} dado su tipo de operación, SIN mencionar el nombre de la empresa dos veces seguidas.
3. Cuarta y quinta oración: conectar ese desafío con los servicios propuestos como solución cohesionada, mencionando al menos 2 servicios específicos.

EXTENSIÓN: entre 120 y 150 palabras exactas.
"""

    return _ollama(prompt, 300)


def generar_analisis_riesgo(empresa, industria, antecedente=""):
    ctx = f"\nContexto específico del cliente:\n{antecedente}" if antecedente else ""

    prompt = f"""{INSTRUCCION_TONO}

TAREA: Escribe el análisis de riesgo cibernético para {empresa} del sector {industria}.
{ctx}

ESTRUCTURA (párrafo corrido, sin títulos ni viñetas):
1. Primera oración: enunciar que el análisis identifica los riesgos principales para este tipo de organización.
2. Riesgo 1: nombrar el riesgo y explicar en una oración cómo impacta operacionalmente a {empresa}.
3. Riesgo 2: nombrar el riesgo y explicar su impacto regulatorio o de reputación.
4. Riesgo 3: nombrar el riesgo y explicar su impacto en continuidad operativa.
5. Última oración: mencionar UNA regulación chilena aplicable (Ley 21.459, Ley 19.628 u otra según industria) y qué obliga a hacer.

TONO: Analítico y objetivo. Serio sin ser alarmista.
EXTENSIÓN: entre 140 y 170 palabras.
"""
    return _ollama(prompt, 340)


def generar_justificacion_servicios(empresa, industria, servicios):
    if len(servicios) <= 3:
        srvs = ", ".join(servicios)
    else:
        srvs = ", ".join(servicios[:-1]) + f" y {servicios[-1]}"

    prompt = f"""{INSTRUCCION_TONO}

TAREA: Escribe la justificación de por qué estos servicios son los adecuados para {empresa}.

DATOS:
- Cliente: {empresa} (sector {industria})
- Servicios: {srvs}

ESTRUCTURA:
1. Primera oración: afirmar que el conjunto de servicios fue seleccionado específicamente para las necesidades de {empresa}.
2. Por cada grupo temático de servicios (máx. 2 grupos): una oración que conecte los servicios con un beneficio concreto de negocio (no técnico).
3. Última oración: mencionar que la implementación fortalece el cumplimiento normativo y la confianza de clientes/usuarios.

EXTENSIÓN: entre 130 y 160 palabras.
"""
    return _ollama(prompt, 320)


def generar_valor_estrategico(empresa, industria, servicios):
    prompt = f"""{INSTRUCCION_TONO}

TAREA: Escribe el párrafo de valor estratégico para {empresa} ({industria}).
Servicios propuestos: {len(servicios)}.

ESTRUCTURA:
1. Primera oración: enmarcar la ciberseguridad como inversión estratégica, no como gasto.
2. Segunda oración: mencionar qué protege concretamente (reputación, continuidad, datos de clientes/usuarios).
3. Tercera oración: plantear el costo de NO actuar de forma objetiva (interrupción operativa, multas, pérdida de confianza).
4. Última oración: cerrar con una afirmación de confianza hacia {empresa} y su capacidad de tomar la decisión correcta.

TONO: Consultor de confianza. Persuasivo sin presión.
EXTENSIÓN: entre 90 y 120 palabras.
"""
    return _ollama(prompt, 240)


def generar_conclusion(empresa, empresa_emisora, contacto, servicios):
    prompt = f"""{INSTRUCCION_TONO}

TAREA: Escribe el párrafo de cierre de la propuesta de ciberseguridad.

DATOS:
- Cliente: {empresa}
- Empresa emisora: {empresa_emisora}
- Contacto del cliente: {contacto}
- Cantidad de servicios: {len(servicios)}

ESTRUCTURA:
1. Primera oración: agradecer la confianza y el tiempo dedicado, sin ser excesivamente formal.
2. Segunda oración: reconocer la importancia del proceso de evaluación y reiterar el compromiso de {empresa_emisora}.
3. Tercera oración: invitar a una reunión de alcance con {contacto} para afinar detalles técnicos y costos.
4. Última oración: expresar disponibilidad inmediata para avanzar.

EXTENSIÓN: entre 70 y 100 palabras.
"""
    return _ollama(prompt, 200)


def generar_frase_clave(empresa, industria):
    prompt = f"""{INSTRUCCION_TONO}

TAREA: Escribe UNA sola frase impactante para destacar en la propuesta de {empresa} ({industria}).

REQUISITOS:
- Debe transmitir que proteger la organización es proteger su misión y futuro.
- Específica para el sector {industria}, no genérica.
- Entre 15 y 30 palabras exactas.
- Sin comillas, sin puntos al final si termina con impacto.
- No usar palabras como "fundamental", "crucial", "esencial" ni "clave".

Solo escribe la frase.
"""
    return _ollama(prompt, 80)


def generar_textos_completos(
    empresa_cliente: str,
    empresa_emisora: str,
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
    print(f"   Empresa emisora: {empresa_emisora}")
    print(f"   Servicios ({len(servicios)}): {', '.join(servicios[:4])}{'...' if len(servicios) > 4 else ''}")
    
    print("  [1/6] Introducción...")
    introduccion = generar_introduccion(empresa_cliente, empresa_emisora, industria, servicios, antecedente)

    print("  [2/6] Análisis de riesgo / alcance...")
    analisis = generar_analisis_riesgo(empresa_cliente, industria, antecedente)

    print("  [3/6] Justificación de servicios...")
    justificacion = generar_justificacion_servicios(empresa_cliente, industria, servicios)

    print("  [4/6] Valor estratégico...")
    valor = generar_valor_estrategico(empresa_cliente, industria, servicios)

    print("  [5/6] Conclusión / cierre...")
    conclusion = generar_conclusion(empresa_cliente, empresa_emisora, contacto or "equipo directivo", servicios)

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


def _reparar_json_comillas(bruto: str) -> str:
    """
    Repara comillas dobles rectas embebidas dentro de un valor de texto
    (la causa más común de JSON inválido generado por el modelo, ej. al
    citar una ley o norma entre comillas). Escapa cualquier comilla que no
    esté cumpliendo el rol estructural de abrir/cerrar una clave o valor
    JSON (es decir, que no esté junto a los separadores típicos : , { } [ ]).
    Respeta las secuencias que ya vienen correctamente escapadas (\\").
    """
    resultado = []
    n = len(bruto)
    i = 0
    while i < n:
        ch = bruto[i]
        if ch == '\\' and i + 1 < n:
            # Ya viene escapado en el texto original -> se respeta tal cual
            resultado.append(ch)
            resultado.append(bruto[i + 1])
            i += 2
            continue
        if ch == '"':
            k = len(resultado) - 1
            while k >= 0 and resultado[k] in ' \t\n':
                k -= 1
            prev = resultado[k] if k >= 0 else ''
            j = i + 1
            while j < n and bruto[j] in ' \t\n':
                j += 1
            nxt = bruto[j] if j < n else ''
            es_estructural = (
                prev in ('', '{', '[', ':', ',') or
                nxt in (':', ',', '}', ']', '')
            )
            if not es_estructural:
                resultado.append('\\"')
                i += 1
                continue
        resultado.append(ch)
        i += 1
    return ''.join(resultado)


def generar_descripcion_servicio(nombre: str, descripcion_base: str, empresa: str, industria: str) -> dict:
    """
    Genera una descripción estructurada (JSON) para un servicio usando Ollama.
    """
    import json

    # Truncar descripción base solo si es extremadamente larga (evita
    # desbordar el contexto del modelo); 6000 caracteres cubre servicios
    # con descripciones muy detalladas de varias fases/actividades/entregables
    # sin perder contenido, como ocurría con el límite anterior de 800.
    desc_truncada = descripcion_base[:6000] if len(descripcion_base) > 6000 else descripcion_base

    prompt = f"""Eres un experto en ciberseguridad redactando una propuesta comercial para {empresa} ({industria}).

Servicio a describir: {nombre}
Descripción base del servicio:
{desc_truncada}

Genera una descripción estructurada en JSON con exactamente esta estructura:
{{
  "intro": "2-3 oraciones que introduzcan el servicio adaptadas a {empresa} del sector {industria}. Tono ejecutivo formal. Sin mencionar el nombre del servicio al inicio.",
  "secciones": [
    {{
      "titulo": "Título de la sección (ejemplo: Fases del Servicio, Actividades Incluidas, Entregables)",
      "items": [
        {{
          "label": "Nombre de la fase o componente",
          "subitems": ["descripción de actividad 1", "descripción de actividad 2", "descripción de actividad 3"]
        }}
      ]
    }}
  ]
}}

REGLAS ESTRICTAS:
- Responde ÚNICAMENTE con el JSON. Sin texto antes, sin texto después, sin bloques de código markdown.
- El campo "intro" es obligatorio y debe estar adaptado a {empresa}.
- Entre 2 y 3 secciones.
- Cada sección debe tener entre 2 y 4 items.
- Cada item debe tener entre 2 y 4 subitems específicos y concretos.
- Todo en español formal chileno.
- Los subitems deben ser descripciones concretas de actividades, no frases genéricas.
- MUY IMPORTANTE PARA QUE EL JSON SEA VÁLIDO: si necesitas citar una ley, norma o nombre propio, NUNCA uses comillas dobles ("). Usa comillas simples (') o directamente sin comillas (ej: Ley 21.663, NERC CIP-002). Las comillas dobles dentro de un texto rompen el formato JSON."""

    try:
        raw = _ollama(prompt, tokens=1400)

        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip().rstrip("```").strip()

        inicio = raw.find("{")
        fin    = raw.rfind("}") + 1
        if inicio == -1 or fin == 0:
            raise ValueError("No se encontró JSON en la respuesta")

        bruto = raw[inicio:fin]
        try:
            data = json.loads(bruto)
        except json.JSONDecodeError:
            try:
                # Intento 1: comillas "tipográficas" (comillas curvas de
                # autocorrección) en vez de comillas simples.
                reparado = (
                    bruto.replace('“', "'").replace('”', "'")
                         .replace('‘', "'").replace('’', "'")
                )
                data = json.loads(reparado)
            except json.JSONDecodeError:
                # Intento 2: comillas dobles rectas embebidas dentro de un
                # valor de texto (ej. citando una ley entre comillas).
                data = json.loads(_reparar_json_comillas(bruto))

        if "intro" not in data or "secciones" not in data:
            raise ValueError("JSON incompleto")
        if not isinstance(data["secciones"], list) or len(data["secciones"]) == 0:
            raise ValueError("Sin secciones")

        return data

    except Exception as e:
        print(f"  ⚠️  generar_descripcion_servicio falló para '{nombre}': {e}. Usando texto plano.")
        return None
