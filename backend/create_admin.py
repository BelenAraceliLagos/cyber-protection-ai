from app.core.database import SessionLocal
from passlib.context import CryptContext

# 1. IMPORTANTE: Importar TODOS los modelos para resolver las relaciones de SQLAlchemy
from app.models.client import Client
from app.models.user import User
from app.models.service import Service
from app.models.quotation import Quotation
from app.models.opportunity import Opportunity
from app.models.milestone import Milestone
from app.models.company import Company 

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def main():
    db = SessionLocal()
    email = "admin@test.com"
    hashed_pwd = pwd_context.hash("admin123")
    
    try:
        user = db.query(User).filter(User.email == email).first()
        
        if user:
            user.hashed_password = hashed_pwd
            print(f"--> Usuario {email} encontrado. ¡Contraseña actualizada a: admin123!")
        else:
            user = User(
                email=email,
                hashed_password=hashed_pwd,
                name="Admin",
                role="admin"
            )
            db.add(user)
            print(f"--> ¡Usuario {email} creado con exito! (Password: admin123)")
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Ocurrió un error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()