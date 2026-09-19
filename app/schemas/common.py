from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Envelope(BaseModel, Generic[T]):
    success: bool = True
    message: str
    data: T | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    errors: dict[str, str] | None = None


class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


def build_page_meta(page: int, page_size: int, total: int) -> PageMeta:
    total_pages = (total + page_size - 1) // page_size if total and page_size else 0
    return PageMeta(page=page, page_size=page_size, total=total, total_pages=total_pages)