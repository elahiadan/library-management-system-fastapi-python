from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.responses import success
from app.dependencies.auth import get_current_active_user
from app.dependencies.permissions import require_admin, require_member
from app.models.borrowing import BorrowingStatus
from app.models.user import User
from app.schemas.borrowing import BorrowingListOut, BorrowOut
from app.schemas.common import Envelope, ErrorResponse, build_page_meta
from app.services import borrowing_service

router = APIRouter(tags=["Borrowings"])

ADMIN_ERRORS = {403: {"model": ErrorResponse}, 401: {"model": ErrorResponse}}
BORROW_ERRORS = {404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 403: {"model": ErrorResponse}}


@router.post(
    "/books/{book_id}/borrow",
    status_code=201,
    response_model=Envelope[BorrowOut],
    responses=BORROW_ERRORS,
    summary="Borrow a book (member)",
)
def borrow(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_member),
):
    borrowing = borrowing_service.borrow_book(db, current_user, book_id)
    return success(
        "Book borrowed successfully", BorrowOut.model_validate(borrowing)
    )


@router.post(
    "/borrowings/{borrowing_id}/return",
    response_model=Envelope[BorrowOut],
    responses=BORROW_ERRORS,
    summary="Return a borrowed book (owner or admin)",
)
def return_book(
    borrowing_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    borrowing = borrowing_service.return_book(db, current_user, borrowing_id)
    return success(
        "Book returned successfully", BorrowOut.model_validate(borrowing)
    )


@router.get(
    "/my/borrowings",
    response_model=Envelope[BorrowingListOut],
    responses=ADMIN_ERRORS,
    summary="List my active borrowings (member)",
)
def my_active_borrowings(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_member),
):
    records, total = borrowing_service.list_active_borrowings(
        db, current_user.id, page, page_size
    )
    return success(
        "Active borrowings retrieved successfully",
        BorrowingListOut(
            items=[BorrowOut.model_validate(r) for r in records],
            meta=build_page_meta(page, page_size, total),
        ),
    )


@router.get(
    "/my/borrowings/history",
    response_model=Envelope[BorrowingListOut],
    responses=ADMIN_ERRORS,
    summary="List my borrowing history (member)",
)
def my_borrowing_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_member),
):
    records, total = borrowing_service.list_borrowing_history(
        db, current_user.id, page, page_size
    )
    return success(
        "Borrowing history retrieved successfully",
        BorrowingListOut(
            items=[BorrowOut.model_validate(r) for r in records],
            meta=build_page_meta(page, page_size, total),
        ),
    )


@router.get(
    "/borrowings",
    response_model=Envelope[BorrowingListOut],
    dependencies=[Depends(require_admin)],
    responses=ADMIN_ERRORS,
    summary="List all borrowings (admin)",
)
def list_all_borrowings(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: BorrowingStatus | None = Query(default=None),
    db: Session = Depends(get_db),
):
    records, total = borrowing_service.list_all_borrowings(db, page, page_size, status)
    return success(
        "Borrowings retrieved successfully",
        BorrowingListOut(
            items=[BorrowOut.model_validate(r) for r in records],
            meta=build_page_meta(page, page_size, total),
        ),
    )


@router.get(
    "/borrowings/overdue",
    response_model=Envelope[BorrowingListOut],
    dependencies=[Depends(require_admin)],
    responses=ADMIN_ERRORS,
    summary="List overdue borrowings (admin)",
)
def list_overdue_borrowings(db: Session = Depends(get_db)):
    records = borrowing_service.list_overdue(db)
    return success(
        "Overdue borrowings retrieved successfully",
        BorrowingListOut(
            items=[BorrowOut.model_validate(r) for r in records],
            meta=build_page_meta(1, len(records), len(records)),
        ),
    )