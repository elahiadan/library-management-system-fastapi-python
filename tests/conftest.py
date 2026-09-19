import os
from datetime import datetime, timedelta, timezone
from itertools import count

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-that-is-long-enough-for-sha256"
os.environ["APP_ENV"] = "test"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.models.author import Author
from app.models.book import Book
from app.models.borrowing import Borrowing, BorrowingStatus
from app.models.user import User, UserRole

_test_engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    bind=_test_engine, autocommit=False, autoflush=False, expire_on_commit=False
)

_isbn_counter = count(1000000000000)


@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=_test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def user_factory(db_session):
    def _make(email="member@example.com", role=UserRole.MEMBER, name="Test Member", is_active=True):
        user = User(
            name=name,
            email=email,
            password_hash=get_password_hash("password123"),
            role=role,
            is_active=is_active,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _make


@pytest.fixture()
def auth_headers():
    def _headers(user):
        token = create_access_token(str(user.id), user.role.value)
        return {"Authorization": f"Bearer {token}"}

    return _headers


@pytest.fixture()
def author_factory(db_session):
    def _make(name="J.K. Rowling", bio="British author"):
        author = Author(name=name, bio=bio)
        db_session.add(author)
        db_session.commit()
        db_session.refresh(author)
        return author

    return _make


@pytest.fixture()
def book_factory(db_session, author_factory):
    def _make(title="Python Programming", author=None, isbn=None, total_copies=3, published_year=2020):
        author = author or author_factory()
        if isbn is None:
            isbn = str(next(_isbn_counter))
        book = Book(
            title=title,
            isbn=isbn,
            description="A test book",
            published_year=published_year,
            total_copies=total_copies,
            available_copies=total_copies,
            author_id=author.id,
        )
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)
        return book

    return _make


@pytest.fixture()
def borrowing_factory(db_session, book_factory):
    def _make(user, book=None, status=BorrowingStatus.BORROWED, returned_at=None, due_at=None):
        book = book or book_factory()
        now = datetime.now(timezone.utc)
        borrowing = Borrowing(
            user_id=user.id,
            book_id=book.id,
            status=status,
            borrowed_at=now,
            returned_at=returned_at,
            due_at=due_at or (now + timedelta(days=14)),
        )
        db_session.add(borrowing)
        db_session.commit()
        db_session.refresh(borrowing)
        return borrowing

    return _make