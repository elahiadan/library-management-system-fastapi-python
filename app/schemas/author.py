from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import PageMeta


def _strip_name(value: str | None) -> str | None:
    if value is None:
        return value
    value = value.strip()
    if not value:
        raise ValueError("name cannot be blank")
    return value


class AuthorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    bio: str | None = Field(default=None, max_length=2000)

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        return _strip_name(value)


class AuthorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    bio: str | None = Field(default=None, max_length=2000)

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str | None) -> str | None:
        return _strip_name(value)


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