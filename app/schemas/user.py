from pydantic import BaseModel, EmailStr
from typing import Optional


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None


class UserAdminCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role_name: str = "user"


class UserAdminUpdate(BaseModel):
    name: Optional[str] = None
    role_name: Optional[str] = None
    is_active: Optional[bool] = None
    new_password: Optional[str] = None


def user_to_response(user) -> dict:
    return {
        "id":        user.id,
        "email":     user.email,
        "name":      user.profile.name if user.profile else "",
        "role":      user.user_roles[0].role.name if user.user_roles else "user",
        "is_active": user.is_active,
    }
