from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import PageMeta


class AuthorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    bio: str | None = Field(default=None, max_length=2000)


class AuthorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    bio: str | None = Field(default=None, max_length=2000)


class AuthorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    bio: str | None
    created_at: datetime
    updated_at: datetime


class AuthorListOut(BaseModel):
    items: list[AuthorOut]
    meta: PageMeta