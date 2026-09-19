from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError, ResourceNotFound
from app.models.author import Author
from app.models.book import Book


def list_authors(db: Session, page: int, page_size: int, search: str | None = None):
    query = select(Author)
    if search:
        query = query.where(Author.name.ilike(f"%{search.strip()}%"))
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    authors = db.scalars(
        query.order_by(Author.name)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return authors, total


def get_author(db: Session, author_id: int) -> Author:
    author = db.get(Author, author_id)
    if author is None:
        raise ResourceNotFound(f"Author with id {author_id} not found")
    return author


def create_author(db: Session, payload) -> Author:
    author = Author(name=payload.name.strip(), bio=payload.bio)
    db.add(author)
    db.commit()
    db.refresh(author)
    return author


def update_author(db: Session, author_id: int, payload) -> Author:
    author = get_author(db, author_id)
    if payload.name is not None:
        author.name = payload.name.strip()
    if payload.bio is not None:
        author.bio = payload.bio
    db.commit()
    db.refresh(author)
    return author


def delete_author(db: Session, author_id: int) -> None:
    author = get_author(db, author_id)
    book_count = db.scalar(
        select(func.count()).select_from(Book).where(Book.author_id == author_id)
    )
    if book_count:
        raise AppError(
            status_code=409, message="Cannot delete an author who has existing books"
        )
    db.delete(author)
    db.commit()