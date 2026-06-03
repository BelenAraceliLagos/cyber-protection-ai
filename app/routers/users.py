from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.user import User, Profile, Role, UserRole
from app.schemas.user import UserAdminCreate, UserAdminUpdate, UserResponse, user_to_response
from app.core.security import hash_password

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db), _=Depends(require_admin)):
    users = db.query(User).order_by(User.id).all()
    return [user_to_response(u) for u in users]


@router.post("/", response_model=UserResponse, status_code=201)
def create_user(
    data: UserAdminCreate,
    db: Session = Depends(get_db),
    _=Depends(require_admin)
):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email ya registrado")

    role = db.query(Role).filter(Role.name == data.role_name).first()
    if not role:
        raise HTTPException(status_code=400, detail="Rol inválido")

    user = User(email=data.email, hashed_password=hash_password(data.password))
    db.add(user)
    db.flush()

    db.add(Profile(user_id=user.id, name=data.name))
    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.commit()
    db.refresh(user)
    return user_to_response(user)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UserAdminUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if data.name is not None and user.profile:
        user.profile.name = data.name

    if data.is_active is not None:
        user.is_active = data.is_active

    if data.new_password:
        user.hashed_password = hash_password(data.new_password)

    if data.role_name is not None:
        role = db.query(Role).filter(Role.name == data.role_name).first()
        if not role:
            raise HTTPException(status_code=400, detail="Rol inválido")
        db.query(UserRole).filter(UserRole.user_id == user_id).delete()
        db.add(UserRole(user_id=user_id, role_id=role.id))

    db.commit()
    db.refresh(user)
    return user_to_response(user)
