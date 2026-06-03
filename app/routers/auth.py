from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserLogin, UserResponse, UserUpdate, user_to_response
from app.core.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    if not db_user.is_active:
        raise HTTPException(status_code=403, detail="Usuario desactivado")

    role_name = db_user.user_roles[0].role.name if db_user.user_roles else "user"
    name      = db_user.profile.name if db_user.profile else db_user.email

    access_token = create_access_token(data={
        "sub":   str(db_user.id),
        "email": db_user.email,
        "role":  role_name,
        "name":  name,
    })

    return {"access_token": access_token, "token_type": "bearer"}


@router.put("/me", response_model=UserResponse)
def update_profile(
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if data.name and current_user.profile:
        current_user.profile.name = data.name

    if data.new_password:
        if not data.current_password:
            raise HTTPException(status_code=400, detail="Debes ingresar tu contraseña actual")
        if not verify_password(data.current_password, current_user.hashed_password):
            raise HTTPException(status_code=400, detail="La contraseña actual es incorrecta")
        current_user.hashed_password = hash_password(data.new_password)

    db.commit()
    db.refresh(current_user)
    return user_to_response(current_user)
