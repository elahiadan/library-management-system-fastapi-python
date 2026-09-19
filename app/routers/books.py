from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.responses import success
from app.dependencies.auth import get_current_active_user
from app.dependencies.permissions import require_admin
from app.models.user import User
from app.schemas.book import BookCreate, BookListOut, BookOut, BookUpdate
from app.schemas.common import Envelope, ErrorResponse, build_page_meta
from app.services import book_service

router = APIRouter(prefix="/books", tags=["Books"])

ADMIN_ERRORS = {403: {"model": ErrorResponse}, 401: {"model": ErrorResponse}}
NOT_FOUND_ERRORS = {404: {"model": ErrorResponse}, **ADMIN_ERRORS}


@router.get(
    "",
    response_model=Envelope[BookListOut],
    responses=NOT_FOUND_ERRORS,
    summary="List and search books (authenticated users)",
)
def list_books(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: str | None = Query(default=None, max_length=100),
    author_id: int | None = Query(default=None),
    available: bool | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    books, total = book_service.list_books(
        db, page, page_size, search, author_id, available
    )
    return success(
        "Books retrieved successfully",
        BookListOut(
            items=[BookOut.model_validate(b) for b in books],
            meta=build_page_meta(page, page_size, total),
        ),
    )


@router.get(
    "/{book_id}",
    response_model=Envelope[BookOut],
    responses=NOT_FOUND_ERRORS,
    summary="Get a book by id (authenticated users)",
)
def get_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    book = book_service.get_book(db, book_id)
    return success("Book retrieved successfully", BookOut.model_validate(book))


@router.post(
    "",
    status_code=201,
    response_model=Envelope[BookOut],
    dependencies=[Depends(require_admin)],
    responses=NOT_FOUND_ERRORS,
    summary="Create a book (admin only)",
)
def create_book(payload: BookCreate, db: Session = Depends(get_db)):
    book = book_service.create_book(db, payload)
    return success("Book created successfully", BookOut.model_validate(book))


@router.put(
    "/{book_id}",
    response_model=Envelope[BookOut],
    dependencies=[Depends(require_admin)],
    responses=NOT_FOUND_ERRORS,
    summary="Update a book (admin only)",
)
def update_book(book_id: int, payload: BookUpdate, db: Session = Depends(get_db)):
    book = book_service.update_book(db, book_id, payload)
    return success("Book updated successfully", BookOut.model_validate(book))


@router.delete(
    "/{book_id}",
    status_code=204,
    dependencies=[Depends(require_admin)],
    responses=NOT_FOUND_ERRORS,
    summary="Delete a book (admin only)",
)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    book_service.delete_book(db, book_id)
    return Response(status_code=204)