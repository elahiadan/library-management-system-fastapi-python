from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.author import Author
from app.models.mixins import TimestampMixin


class Book(TimestampMixin, Base):
    __tablename__ = "books"
    __table_args__ = (
        CheckConstraint(
            "available_copies <= total_copies",
            name="ck_books_available_lte_total",
        ),
        CheckConstraint(
            "available_copies >= 0",
            name="ck_books_available_non_negative",
        ),
        CheckConstraint(
            "total_copies >= 0",
            name="ck_books_total_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    isbn: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_year: Mapped[int] = mapped_column(Integer, nullable=False)
    total_copies: Mapped[int] = mapped_column(Integer, nullable=False)
    available_copies: Mapped[int] = mapped_column(Integer, nullable=False)
    author_id: Mapped[int] = mapped_column(
        ForeignKey("authors.id", ondelete="RESTRICT"), index=True, nullable=False
    )

    author: Mapped[Author] = relationship(back_populates="books")
    borrowings: Mapped[list["Borrowing"]] = relationship(back_populates="book")