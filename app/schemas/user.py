from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import UserRole
from app.schemas.common import PageMeta


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserListOut(BaseModel):
    items: list[UserOut]
    meta: PageMeta