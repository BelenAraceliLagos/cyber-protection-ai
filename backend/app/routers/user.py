from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import hash_password
from app.models.user import User
from app.models.quotation import Quotation
from app.schemas.user import UserAdminCreate, UserAdminUpdate, UserResponse

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

VALID_ROLES = {"admin", "user"}


def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def normalize_role(role: str):
    normalized = (role or "user").strip().lower()
    if normalized not in VALID_ROLES:
        raise HTTPException(
            status_code=400,
            detail="Invalid role"
        )
    return normalized


@router.get("/", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    return db.query(User).order_by(User.id.asc()).all()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserAdminCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    name = data.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name cannot be empty")

    if len(data.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters"
        )

    new_user = User(
        name=name,
        email=data.email,
        role=normalize_role(data.role),
        hashed_password=hash_password(data.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UserAdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if data.email is not None and data.email != user.email:
        existing_user = db.query(User).filter(User.email == data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        user.email = data.email

    if data.name is not None:
        name = data.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="Name cannot be empty")
        user.name = name

    if data.role is not None:
        user.role = normalize_role(data.role)

    if data.new_password:
        if len(data.new_password) < 8:
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 8 characters"
            )
        user.hashed_password = hash_password(data.new_password)

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="You cannot delete your own user"
        )

    has_quotations = db.query(Quotation).filter(
        Quotation.created_by == user.id
    ).first()

    if has_quotations:
        raise HTTPException(
            status_code=400,
            detail="User has related quotations and cannot be deleted"
        )

    db.delete(user)
    db.commit()
