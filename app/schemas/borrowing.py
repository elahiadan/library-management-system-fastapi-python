from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.borrowing import BorrowingStatus
from app.schemas.book import BookOut
from app.schemas.common import PageMeta
from app.schemas.user import UserOut


class BorrowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    book_id: int
    borrowed_at: datetime
    due_at: datetime
    returned_at: datetime | None
    status: BorrowingStatus
    user: UserOut
    book: BookOut
    created_at: datetime
    updated_at: datetime


class BorrowingListOut(BaseModel):
    items: list[BorrowOut]
    meta: PageMeta