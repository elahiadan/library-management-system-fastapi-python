"""create library tables

Revision ID: 0001
Revises:
Create Date: 2026-09-18
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    user_role = sa.Enum("ADMIN", "MEMBER", name="user_role", native_enum=False, length=20)
    borrowing_status = sa.Enum(
        "BORROWED", "RETURNED", "OVERDUE",
        name="borrowing_status", native_enum=False, length=20,
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False, server_default="MEMBER"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "authors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_authors_name", "authors", ["name"])

    op.create_table(
        "books",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("isbn", sa.String(length=20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("published_year", sa.Integer(), nullable=False),
        sa.Column("total_copies", sa.Integer(), nullable=False),
        sa.Column("available_copies", sa.Integer(), nullable=False),
        sa.Column(
            "author_id",
            sa.Integer(),
            sa.ForeignKey("authors.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "available_copies <= total_copies",
            name="ck_books_available_lte_total",
        ),
        sa.CheckConstraint(
            "available_copies >= 0",
            name="ck_books_available_non_negative",
        ),
        sa.CheckConstraint(
            "total_copies >= 0",
            name="ck_books_total_non_negative",
        ),
    )
    op.create_index("ix_books_isbn", "books", ["isbn"], unique=True)
    op.create_index("ix_books_author_id", "books", ["author_id"])
    op.create_index("ix_books_title", "books", ["title"])

    op.create_table(
        "borrowings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "book_id",
            sa.Integer(),
            sa.ForeignKey("books.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("borrowed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("returned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", borrowing_status, nullable=False, server_default="BORROWED"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_borrowings_user_id", "borrowings", ["user_id"])
    op.create_index("ix_borrowings_book_id", "borrowings", ["book_id"])
    op.create_index("ix_borrowings_due_at", "borrowings", ["due_at"])
    op.create_index("ix_borrowings_status", "borrowings", ["status"])


def downgrade() -> None:
    op.drop_table("borrowings")
    op.drop_table("books")
    op.drop_table("authors")
    op.drop_table("users")