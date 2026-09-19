from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.exceptions import (
    AuthorizationError,
    BookUnavailable,
    BorrowingLimitExceeded,
    InvalidBorrowingState,
    ResourceNotFound,
)
from app.models.book import Book
from app.models.borrowing import Borrowing, BorrowingStatus
from app.models.user import User, UserRole

_BORROWING_LOADS = (
    selectinload(Borrowing.book).selectinload(Book.author),
    selectinload(Borrowing.user),
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _is_overdue(record: Borrowing, now: datetime) -> bool:
    if record.returned_at is not None:
        return False
    return _as_utc(record.due_at) < now


def _mark_effective_statuses(records: list[Borrowing]) -> None:
    """Overdue is derived at read time; the DB write path only sets BORROWED/RETURNED."""
    now = _now()
    for record in records:
        if _is_overdue(record, now):
            record.status = BorrowingStatus.OVERDUE


def borrow_book(db: Session, user: User, book_id: int) -> Borrowing:
    # Serialize per user so the active-count and duplicate checks below are race-free.
    locked_user = db.scalar(
        select(User).where(User.id == user.id).with_for_update()
    )
    if locked_user is None:
        raise ResourceNotFound(f"User with id {user.id} not found")

    book = db.scalar(select(Book).where(Book.id == book_id).with_for_update())
    if book is None:
        raise ResourceNotFound(f"Book with id {book_id} not found")
    if book.available_copies <= 0:
        raise BookUnavailable()

    active_count = db.scalar(
        select(func.count())
        .select_from(Borrowing)
        .where(Borrowing.user_id == user.id, Borrowing.returned_at.is_(None))
    )
    if active_count >= settings.max_active_borrowings:
        raise BorrowingLimitExceeded(
            f"Maximum {settings.max_active_borrowings} active borrowings per member"
        )

    already_borrowed = db.scalar(
        select(Borrowing.id).where(
            Borrowing.user_id == user.id,
            Borrowing.book_id == book.id,
            Borrowing.returned_at.is_(None),
        )
    )
    if already_borrowed is not None:
        raise InvalidBorrowingState(
            "You already have an active borrowing for this book"
        )

    now = _now()
    borrowing = Borrowing(
        user_id=user.id,
        book_id=book.id,
        status=BorrowingStatus.BORROWED,
        borrowed_at=now,
        due_at=now + timedelta(days=settings.borrow_duration_days),
        returned_at=None,
    )
    book.available_copies -= 1
    db.add(borrowing)
    db.commit()
    db.refresh(borrowing)
    return borrowing


def return_book(db: Session, current_user: User, borrowing_id: int) -> Borrowing:
    # Row lock makes the state check -> stock increment atomic for this borrowing.
    borrowing = db.scalar(
        select(Borrowing)
        .where(Borrowing.id == borrowing_id)
        .options(*_BORROWING_LOADS)
        .with_for_update()
    )
    if borrowing is None:
        raise ResourceNotFound(f"Borrowing with id {borrowing_id} not found")

    if current_user.role != UserRole.ADMIN and borrowing.user_id != current_user.id:
        raise AuthorizationError("You can only return your own borrowings")
    if borrowing.returned_at is not None or borrowing.status == BorrowingStatus.RETURNED:
        raise InvalidBorrowingState("This borrowing has already been returned")

    # Lock the book row too, so two concurrent returns of different copies of the
    # same book cannot lose an available_copies increment.
    book = db.scalar(
        select(Book).where(Book.id == borrowing.book_id).with_for_update()
    )
    borrowing.returned_at = _now()
    borrowing.status = BorrowingStatus.RETURNED
    book.available_copies += 1

    db.commit()
    db.refresh(borrowing)
    return borrowing


def list_active_borrowings(db: Session, user_id: int, page: int, page_size: int):
    query = (
        select(Borrowing)
        .where(Borrowing.user_id == user_id, Borrowing.returned_at.is_(None))
        .order_by(Borrowing.borrowed_at.desc())
    )
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    records = db.scalars(
        query.options(*_BORROWING_LOADS)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    _mark_effective_statuses(records)
    return records, total


def list_borrowing_history(db: Session, user_id: int, page: int, page_size: int):
    query = (
        select(Borrowing)
        .where(Borrowing.user_id == user_id)
        .order_by(Borrowing.borrowed_at.desc())
    )
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    records = db.scalars(
        query.options(*_BORROWING_LOADS)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    _mark_effective_statuses(records)
    return records, total


def list_all_borrowings(
    db: Session, page: int, page_size: int, status: BorrowingStatus | None = None
):
    now = _now()
    query = select(Borrowing)
    if status == BorrowingStatus.OVERDUE:
        query = query.where(Borrowing.returned_at.is_(None), Borrowing.due_at < now)
    elif status == BorrowingStatus.BORROWED:
        query = query.where(Borrowing.returned_at.is_(None), Borrowing.due_at >= now)
    elif status == BorrowingStatus.RETURNED:
        query = query.where(Borrowing.returned_at.is_not(None))
    elif status is not None:
        query = query.where(Borrowing.status == status)

    total = db.scalar(select(func.count()).select_from(query.subquery()))
    records = db.scalars(
        query.options(*_BORROWING_LOADS)
        .order_by(Borrowing.borrowed_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    _mark_effective_statuses(records)
    return records, total


def list_overdue(db: Session):
    now = _now()
    records = db.scalars(
        select(Borrowing)
        .where(Borrowing.returned_at.is_(None), Borrowing.due_at < now)
        .options(*_BORROWING_LOADS)
        .order_by(Borrowing.borrowed_at.desc())
    ).all()
    _mark_effective_statuses(records)
    return records