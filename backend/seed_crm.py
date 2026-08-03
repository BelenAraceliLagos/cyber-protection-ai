import random
from datetime import datetime, timedelta, timezone

from app.core.database import SessionLocal

# Importar todos los modelos de SQLAlchemy para evitar errores de relación
from app.models.client import Client
from app.models.user import User
from app.models.service import Service
from app.models.quotation import Quotation
from app.models.opportunity import Opportunity
from app.models.company import Company
from app.models.milestone import Milestone
from app.models.quotation_item import QuotationItem

ETAPAS = ["prospecto", "propuesta", "negociacion", "aprobacion", "ganado", "perdido"]
ORIGENES = ["referido", "busqueda_organica", "redes_sociales", "email_marketing", "trafico_directo", "evento"]

EMPRESAS_MOCK = [
    ("Sistemas Globales SpA", "contacto@sglobal.cl"),
    ("Inversiones Alpha Ltda", "ventas@inversionesalpha.cl"),
    ("Consultora Bicentenario", "info@cbicentenario.cl"),
    ("Logística del Pacífico", "operaciones@logpacific.cl"),
    ("Fintech Vision Chile", "contacto@fintechvision.cl"),
    ("EcoEnergy Solutions", "admin@ecoenergy.cl"),
    ("Retail Multimarcas", "compras@retailmulti.cl"),
    ("Servicios Mineros Norte", "proyectos@smineros.cl"),
    ("AgroIndustria Sur", "contacto@agrosur.cl"),
    ("Salud Integral Digital", "tecnologia@saludid.cl")
]

SERVICIOS_MOCK = [
    ("Pentesting Web & API", "Evaluación de vulnerabilidades y pruebas de penetración en aplicaciones web y APIs.", 120.0),
    ("SOC 24/7 Managed Security", "Centro de operaciones de seguridad administrado las 24 horas del día.", 250.0),
    ("Auditoría ISO 27001 / SGSI", "Implementación y auditoría para la certificación ISO 27001.", 180.0),
    ("Simulación Phishing y Concientización", "Campañas de phishing simulado y entrenamiento continuo del personal.", 65.0),
    ("Hardening Cloud AWS & Azure", "Aseguramiento de arquitectura en la nube e infraestructura crítica.", 150.0),
    ("Análisis de Vulnerabilidades Continuo", "Scans periódicos y gestión activa de parches de seguridad.", 90.0),
    ("Respuesta a Incidentes y Forense", "Servicio especializado de contención de incidentes y análisis forense.", 300.0),
    ("CISO as a Service", "Asesoría ejecutiva estratégica en ciberseguridad por demanda.", 200.0)
]

def seed_data():
    db = SessionLocal()
    print("[+] Generando datos de prueba para el CRM...")

    try:
        clients_created = []

        # 1. Crear 10 Clientes de prueba
        for company_name, email in EMPRESAS_MOCK:
            client = db.query(Client).filter(Client.email == email).first()
            if not client:
                client = Client(
                    company_name=company_name,
                    contact_name=f"Contacto {company_name.split()[0]}",
                    email=email,
                    phone="+56912345678",
                    origen=random.choice(ORIGENES),
                    lifecycle_stage=random.choice(["lead", "oportunidad", "cliente", "promotor"])
                )
                db.add(client)
                db.commit()
                db.refresh(client)
            clients_created.append(client)

        print(f"[OK] {len(clients_created)} Clientes listos en la Base de Datos.")

        # 2. Crear Servicios de prueba
        services_created = []
        for s_name, s_desc, s_price in SERVICIOS_MOCK:
            srv = db.query(Service).filter(Service.name == s_name).first()
            if not srv:
                srv = Service(
                    name=s_name,
                    description=s_desc,
                    base_price=s_price,
                    active=True
                )
                db.add(srv)
                db.commit()
                db.refresh(srv)
            services_created.append(srv)

        print(f"[OK] {len(services_created)} Servicios listos en la Base de Datos.")

        # 3. Crear 20 Oportunidades distribuidas en el Funnel
        opps_created = 0
        for i in range(1, 21):
            cliente_random = random.choice(clients_created)
            etapa = random.choice(ETAPAS)
            valor_uf = round(random.uniform(50.0, 1500.0), 1)  # Entre 50 y 1500 UF
            
            probabilidades = {
                "prospecto": 20,
                "propuesta": 40,
                "negociacion": 60,
                "aprobacion": 80,
                "ganado": 100,
                "perdido": 0
            }

            fecha_creacion = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 150))

            opp = Opportunity(
                cliente_id=cliente_random.id,
                titulo=f"Proyecto {i} - {cliente_random.company_name}",
                etapa=etapa,
                probabilidad=probabilidades[etapa],
                valor_uf=valor_uf,
                notas=f"Oportunidad de prueba #{i} generada para métricas ejecutivas.",
                created_at=fecha_creacion
            )
            db.add(opp)
            opps_created += 1

        db.commit()
        print(f"[OK] Se crearon {opps_created} oportunidades de prueba.")

        # 4. Crear Cotizaciones de prueba distribuidas en los últimos 6 meses
        quotations_created = 0
        
        # Ponderación alta para 'accepted' para asegurar datos en servicios contratados
        statuses = ["accepted", "accepted", "accepted", "sent", "draft", "rejected"]

        # Obtener un ID de usuario válido para asignar a created_by
        user = db.query(User).first()
        user_id = user.id if user else None

        for q_idx in range(1, 40):
            client = random.choice(clients_created)
            days_ago = random.randint(1, 175)
            q_date = datetime.now(timezone.utc) - timedelta(days=days_ago)

            quotation = Quotation(
                client_id=client.id,
                created_by=user_id,
                status=random.choice(statuses),
                created_at=q_date
            )
            db.add(quotation)
            db.flush()

            # Agregar entre 1 y 3 servicios a la cotización
            num_items = random.randint(1, 3)
            selected_services = random.sample(services_created, num_items)
            subtotal = 0.0

            for srv in selected_services:
                qty = random.randint(1, 3)
                price = srv.base_price
                item_total = price * qty
                subtotal += item_total

                q_item = QuotationItem(
                    quotation_id=quotation.id,
                    service_id=srv.id,
                    quantity=qty,
                    price=price
                )
                db.add(q_item)

            tax = subtotal * 0.19
            total = subtotal + tax
            quotation.subtotal = round(subtotal, 2)
            quotation.tax = round(tax, 2)
            quotation.total = round(total, 2)
            quotations_created += 1

        db.commit()
        print(f"[OK] Se crearon {quotations_created} cotizaciones con sus items de servicio.")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error al poblar la base de datos: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()