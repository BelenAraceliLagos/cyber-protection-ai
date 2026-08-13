import random
from datetime import datetime, timedelta, timezone

from app.core.database import SessionLocal

# Importar todos los modelos de SQLAlchemy para evitar errores de relación e interactuar con ellos
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
    ("Sistemas Globales SpA", "contacto@sglobal.cl", "lead"),
    ("Inversiones Alpha Ltda", "ventas@inversionesalpha.cl", "oportunidad"),
    ("Consultora Bicentenario", "info@cbicentenario.cl", "cliente"),
    ("Logística del Pacífico", "operaciones@logpacific.cl", "cliente"),
    ("Fintech Vision Chile", "contacto@fintechvision.cl", "promotor"),
    ("EcoEnergy Solutions", "admin@ecoenergy.cl", "lead"),
    ("Retail Multimarcas", "compras@retailmulti.cl", "oportunidad"),
    ("Servicios Mineros Norte", "proyectos@smineros.cl", "cliente"),
    ("AgroIndustria Sur", "contacto@agrosur.cl", "promotor"),
    ("Salud Integral Digital", "tecnologia@saludid.cl", "cliente"),
    ("Constructora Andina", "contacto@candina.cl", "lead"),
    ("Transportes Meridian", "contacto@tmeridian.cl", "oportunidad"),
    ("Alimentos del Maule", "contacto@almaule.cl", "cliente"),
    ("Minería del Sol", "operaciones@msol.cl", "cliente"),
    ("Pesquera Austral", "ventas@paustral.cl", "promotor"),
    ("Banca Futura SpA", "innovacion@bfutura.cl", "oportunidad"),
    ("Clínica Santa María Digital", "ti@csantamariadigital.cl", "cliente"),
    ("Vitivinícola del Sur", "contacto@vsur.cl", "lead"),
    ("Aseguradora Patagonia", "soporte@apatagonia.cl", "oportunidad"),
    ("Desarrollos Inmobiliarios", "ventas@dinmobiliarios.cl", "cliente"),
    ("Tecnología Inteligente", "info@tecinteligente.cl", "promotor"),
    ("Soluciones IoT Chile", "contacto@iotchile.cl", "lead"),
    ("Retail Express", "compras@retailexpress.cl", "oportunidad"),
    ("Energías del Desierto", "contacto@edesierto.cl", "cliente"),
    ("Pesca y Conservas Ltda", "info@pescayconservas.cl", "cliente")
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
    print("[+] Generando datos de prueba limpios y realistas para el CRM...")

    try:
        # Limpieza previa de tablas relacionadas para permitir re-ejecución limpia
        print("[-] Limpiando tablas de CRM anteriores...")
        db.query(QuotationItem).delete()
        db.query(Quotation).delete()
        db.query(Opportunity).delete()
        db.query(Client).delete()
        db.query(Service).delete()
        db.commit()

        clients_created = []

        # 1. Crear 25 Clientes de prueba con distribución de orígenes y etapas
        for company_name, email, default_stage in EMPRESAS_MOCK:
            client = Client(
                company_name=company_name,
                contact_name=f"Contacto {company_name.split()[0]}",
                email=email,
                phone="+569" + "".join([str(random.randint(0, 9)) for _ in range(8)]),
                origen=random.choice(ORIGENES),
                lifecycle_stage=default_stage
            )
            db.add(client)
            db.commit()
            db.refresh(client)
            clients_created.append(client)

        print(f"[OK] {len(clients_created)} Clientes creados con éxito.")

        # 2. Crear Servicios de prueba
        services_created = []
        for s_name, s_desc, s_price in SERVICIOS_MOCK:
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

        print(f"[OK] {len(services_created)} Servicios creados con éxito.")

        # 3. Crear 40 Oportunidades distribuidas en el Funnel con tendencia mensual
        # Queremos mostrar un crecimiento en oportunidades creadas mes a mes
        opps_created = 0
        hoy = datetime.now(timezone.utc)
        
        # Generar oportunidades en los últimos 6 meses (de más antiguo a más reciente)
        # Meses atrás: 5, 4, 3, 2, 1, 0 (actual)
        distribucion_mensual_opps = [4, 5, 6, 8, 10, 12] # Crecimiento en el pipeline
        
        probabilidades = {
            "prospecto": 20,
            "propuesta": 40,
            "negociacion": 60,
            "aprobacion": 80,
            "ganado": 100,
            "perdido": 0
        }

        opportunity_idx = 1
        for meses_atras, cantidad in enumerate(distribucion_mensual_opps):
            # Calcular rango de días para este mes en particular
            dias_max = (5 - meses_atras) * 30 + 30
            dias_min = (5 - meses_atras) * 30
            
            for _ in range(cantidad):
                cliente_random = random.choice(clients_created)
                etapa = random.choice(ETAPAS)
                
                # Asignar etapa coherente si el cliente es promotor/cliente
                if cliente_random.lifecycle_stage in ["cliente", "promotor"] and random.random() < 0.7:
                    etapa = "ganado"
                
                valor_uf = round(random.uniform(80.0, 1800.0), 1)
                dias_ago = random.randint(dias_min, dias_max)
                fecha_creacion = hoy - timedelta(days=dias_ago)

                opp = Opportunity(
                    cliente_id=cliente_random.id,
                    titulo=f"Proyecto {opportunity_idx} - {cliente_random.company_name}",
                    etapa=etapa,
                    probabilidad=probabilidades[etapa],
                    valor_uf=valor_uf,
                    notas=f"Oportunidad de prueba #{opportunity_idx} generada para métricas del CRM.",
                    created_at=fecha_creacion
                )
                db.add(opp)
                opportunity_idx += 1
                opps_created += 1

        db.commit()
        print(f"[OK] Se crearon {opps_created} oportunidades con tendencia temporal.")

        # 4. Crear 60 Cotizaciones con items de servicios, distribuidas en los últimos 6 meses
        quotations_created = 0
        
        # Ponderación alta para 'accepted' para asegurar datos en servicios contratados
        statuses = ["accepted", "accepted", "accepted", "sent", "sent", "draft", "rejected"]

        # Obtener un ID de usuario válido para asignar a created_by
        user = db.query(User).first()
        user_id = user.id if user else None

        # Distribución de cotizaciones en los últimos 6 meses
        distribucion_mensual_quots = [6, 8, 9, 11, 12, 14]
        
        quotation_idx = 1
        for meses_atras, cantidad in enumerate(distribucion_mensual_quots):
            dias_max = (5 - meses_atras) * 30 + 30
            dias_min = (5 - meses_atras) * 30
            
            for _ in range(cantidad):
                client = random.choice(clients_created)
                dias_ago = random.randint(dias_min, dias_max)
                q_date = hoy - timedelta(days=dias_ago)
                status = random.choice(statuses)

                # Si el cliente ya está en etapa cliente/promotor, forzamos cotización aceptada a menudo
                if client.lifecycle_stage in ["cliente", "promotor"] and random.random() < 0.8:
                    status = "accepted"

                quotation = Quotation(
                    client_id=client.id,
                    created_by=user_id,
                    status=status,
                    created_at=q_date
                )
                db.add(quotation)
                db.flush()

                # Agregar entre 1 y 3 servicios a la cotización
                num_items = random.randint(1, 3)
                selected_services = random.sample(services_created, num_items)
                subtotal = 0.0

                for srv in selected_services:
                    qty = random.randint(1, 2)
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
                quotation_idx += 1

        db.commit()
        print(f"[OK] Se crearon {quotations_created} cotizaciones con distribución mensual y servicios asociados.")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error al poblar la base de datos: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()