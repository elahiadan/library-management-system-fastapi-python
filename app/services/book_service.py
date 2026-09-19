from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import AppError, DuplicateResource, ResourceNotFound
from app.models.author import Author
from app.models.book import Book
from app.models.borrowing import Borrowing


def _build_query(search=None, author_id=None, available=None):
    query = select(Book).join(Author, Book.author_id == Author.id)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(
            or_(
                Book.title.ilike(pattern),
                Book.description.ilike(pattern),
                Author.name.ilike(pattern),
            )
        )
    if author_id is not None:
        query = query.where(Book.author_id == author_id)
    if available is not None:
        if available:
            query = query.where(Book.available_copies > 0)
        else:
            query = query.where(Book.available_copies == 0)
    return query


def list_books(
    db: Session,
    page: int,
    page_size: int,
    search: str | None = None,
    author_id: int | None = None,
    available: bool | None = None,
):
    query = _build_query(search, author_id, available)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    books = db.scalars(
        query.options(selectinload(Book.author))
        .order_by(Book.title)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return books, total


def get_book(db: Session, book_id: int) -> Book:
    book = db.scalar(
        select(Book).where(Book.id == book_id).options(selectinload(Book.author))
    )
    if book is None:
        raise ResourceNotFound(f"Book with id {book_id} not found")
    return book


def _ensure_author_exists(db: Session, author_id: int) -> None:
    if db.get(Author, author_id) is None:
        raise ResourceNotFound(f"Author with id {author_id} not found")


def _ensure_isbn_unique(db: Session, isbn: str, exclude_id: int | None = None) -> None:
    query = select(Book).where(Book.isbn == isbn)
    if exclude_id is not None:
        query = query.where(Book.id != exclude_id)
    if db.scalar(query) is not None:
        raise DuplicateResource("A book with this ISBN already exists")


def create_book(db: Session, payload) -> Book:
    _ensure_author_exists(db, payload.author_id)
    _ensure_isbn_unique(db, payload.isbn)

    book = Book(
        title=payload.title.strip(),
        isbn=payload.isbn,
        description=payload.description,
        published_year=payload.published_year,
        total_copies=payload.total_copies,
        available_copies=payload.total_copies,
        author_id=payload.author_id,
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def update_book(db: Session, book_id: int, payload) -> Book:
    book = db.scalar(
        select(Book)
        .where(Book.id == book_id)
        .options(selectinload(Book.author))
        .with_for_update()
    )
    if book is None:
        raise ResourceNotFound(f"Book with id {book_id} not found")

    if payload.author_id is not None:
        _ensure_author_exists(db, payload.author_id)
    if payload.isbn is not None and payload.isbn != book.isbn:
        _ensure_isbn_unique(db, payload.isbn, exclude_id=book.id)

    if payload.title is not None:
        book.title = payload.title.strip()
    if payload.isbn is not None:
        book.isbn = payload.isbn
    if payload.description is not None:
        book.description = payload.description
    if payload.published_year is not None:
        book.published_year = payload.published_year
    if payload.total_copies is not None:
        borrowed_copies = book.total_copies - book.available_copies
        if payload.total_copies < borrowed_copies:
            raise AppError(
                status_code=400,
                message="total_copies cannot be less than the number of copies currently on loan",
            )
        book.available_copies += payload.total_copies - book.total_copies
        book.total_copies = payload.total_copies

    db.commit()
    db.refresh(book)
    return book


def delete_book(db: Session, book_id: int) -> None:
    book = get_book(db, book_id)
    borrowing_count = db.scalar(
        select(func.count()).select_from(Borrowing).where(Borrowing.book_id == book_id)
    )
    if borrowing_count:
        raise AppError(
            status_code=409,
            message="Cannot delete a book that has borrowing history",
        )
    db.delete(book)
    db.commit()