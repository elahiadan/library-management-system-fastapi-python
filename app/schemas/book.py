from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.validators import normalize_isbn
from app.schemas.author import AuthorOut
from app.schemas.common import PageMeta


class BookCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    isbn: str
    description: str | None = Field(default=None, max_length=5000)
    published_year: int = Field(ge=1000, le=2100)
    total_copies: int = Field(ge=0)
    author_id: int

    @field_validator("title")
    @classmethod
    def _validate_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("title cannot be blank")
        return value

    @field_validator("isbn")
    @classmethod
    def _validate_isbn(cls, value: str) -> str:
        return normalize_isbn(value)


class BookUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    isbn: str | None = None
    description: str | None = Field(default=None, max_length=5000)
    published_year: int | None = Field(default=None, ge=1000, le=2100)
    total_copies: int | None = Field(default=None, ge=0)
    author_id: int | None = None

    @field_validator("title")
    @classmethod
    def _validate_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("title cannot be blank")
        return value

    @field_validator("isbn")
    @classmethod
    def _validate_isbn(cls, value):
        if value is None:
            return value
        return normalize_isbn(value)


class BookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    isbn: str
    description: str | None
    published_year: int
    total_copies: int
    available_copies: int
    author: AuthorOut
    created_at: datetime
    updated_at: datetime


class BookListOut(BaseModel):
    items: list[BookOut]
    meta: PageMeta