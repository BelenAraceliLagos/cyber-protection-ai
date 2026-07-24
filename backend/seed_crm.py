import random
from datetime import datetime, timedelta

from app.core.database import SessionLocal

# Importar todos los modelos de SQLAlchemy para evitar errores de relación
from app.models.client import Client
from app.models.user import User
from app.models.service import Service
from app.models.quotation import Quotation
from app.models.opportunity import Opportunity
from app.models.company import Company
from app.models.milestone import Milestone

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

def seed_data():
    db = SessionLocal()
    print("🌱 Generando datos de prueba para el CRM...")

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

        print(f"✅ {len(clients_created)} Clientes listos en la Base de Datos.")

        # 2. Crear 20 Oportunidades distribuidas en el Funnel
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

            fecha_creacion = datetime.utcnow() - timedelta(days=random.randint(1, 120))

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
        print(f"🚀 ¡Éxito! Se crearon {opps_created} oportunidades de prueba en la base de datos.")

    except Exception as e:
        db.rollback()
        print(f"❌ Error al poblar la base de datos: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()