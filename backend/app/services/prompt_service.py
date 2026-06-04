from app.models.client import Client
from app.models.quotation import Quotation

def build_quotation_prompt(
    client: Client,
    quotation: Quotation
):

    services_text = ""

    for item in quotation.items:

        services_text += f"""
        - Servicio: {item.service.name}
        - Cantidad: {item.quantity}
        - Precio: ${item.price}
        """

    prompt = f"""
    Eres un experto en ciberseguridad y preventa.

    Debes generar un informe profesional
    de propuesta comercial para un cliente.

    INFORMACIÓN CLIENTE:
    Empresa: {client.company_name}
    Contacto: {client.contact_name}
    Industria: {client.industry}

    SERVICIOS COTIZADOS:
    {services_text}

    TOTAL PROPUESTA:
    ${quotation.total}

    Genera:

    1. Introducción profesional
    2. Riesgos de seguridad
    3. Beneficios de los servicios
    4. Descripción técnica
    5. Recomendaciones
    6. Conclusión profesional

    El tono debe ser corporativo y profesional.
    """

    return prompt