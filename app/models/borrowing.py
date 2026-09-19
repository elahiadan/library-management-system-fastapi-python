import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class BorrowingStatus(str, enum.Enum):
    BORROWED = "BORROWED"
    RETURNED = "RETURNED"
    OVERDUE = "OVERDUE"


class Borrowing(TimestampMixin, Base):
    __tablename__ = "borrowings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    borrowed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    due_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    returned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[BorrowingStatus] = mapped_column(
        Enum(BorrowingStatus, name="borrowing_status", native_enum=False, length=20),
        default=BorrowingStatus.BORROWED,
        nullable=False,
        index=True,
    )

    user: Mapped["User"] = relationship(back_populates="borrowings")
    book: Mapped["Book"] = relationship(back_populates="borrowings")