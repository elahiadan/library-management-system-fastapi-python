from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class Author(TimestampMixin, Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)

    books: Mapped[list["Book"]] = relationship(back_populates="author")