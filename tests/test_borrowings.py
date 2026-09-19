from datetime import datetime, timedelta, timezone

from app.models.borrowing import Borrowing, BorrowingStatus
from app.models.user import UserRole
from app.models.book import Book


def test_borrow_available_book(client, user_factory, book_factory, auth_headers):
    member = user_factory()
    book = book_factory(total_copies=2)
    response = client.post(f"/api/books/{book.id}/borrow", headers=auth_headers(member))
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["status"] == "BORROWED"
    assert data["returned_at"] is None
    due = datetime.fromisoformat(data["due_at"])
    if due.tzinfo is None:
        due = due.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    assert (due - now) >= timedelta(days=13)

    book_data = client.get(f"/api/books/{book.id}", headers=auth_headers(member)).json()["data"]
    assert book_data["available_copies"] == 1


def test_cannot_borrow_unavailable_book(client, user_factory, book_factory, auth_headers):
    member_a = user_factory(email="a@example.com")
    member_b = user_factory(email="b@example.com")
    book = book_factory(total_copies=1)
    assert client.post(f"/api/books/{book.id}/borrow", headers=auth_headers(member_a)).status_code == 201
    response = client.post(f"/api/books/{book.id}/borrow", headers=auth_headers(member_b))
    assert response.status_code == 409


def test_cannot_borrow_same_book_twice(client, user_factory, book_factory, auth_headers):
    member = user_factory()
    book = book_factory(total_copies=3)
    assert client.post(f"/api/books/{book.id}/borrow", headers=auth_headers(member)).status_code == 201
    assert client.post(f"/api/books/{book.id}/borrow", headers=auth_headers(member)).status_code == 409


def test_max_three_active_borrowings(client, user_factory, book_factory, auth_headers):
    member = user_factory()
    books = [book_factory(title=f"Book {i}") for i in range(4)]
    for book in books[:3]:
        assert client.post(f"/api/books/{book.id}/borrow", headers=auth_headers(member)).status_code == 201
    response = client.post(f"/api/books/{books[3].id}/borrow", headers=auth_headers(member))
    assert response.status_code == 409


def test_return_book(client, user_factory, book_factory, auth_headers):
    member = user_factory()
    book = book_factory(total_copies=2)
    borrowing_id = client.post(
        f"/api/books/{book.id}/borrow", headers=auth_headers(member)
    ).json()["data"]["id"]

    response = client.post(
        f"/api/borrowings/{borrowing_id}/return", headers=auth_headers(member)
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "RETURNED"
    assert data["returned_at"] is not None

    book_data = client.get(f"/api/books/{book.id}", headers=auth_headers(member)).json()["data"]
    assert book_data["available_copies"] == 2


def test_cannot_return_twice(client, user_factory, book_factory, auth_headers):
    member = user_factory()
    book = book_factory()
    borrowing_id = client.post(
        f"/api/books/{book.id}/borrow", headers=auth_headers(member)
    ).json()["data"]["id"]
    url = f"/api/borrowings/{borrowing_id}/return"
    assert client.post(url, headers=auth_headers(member)).status_code == 200
    assert client.post(url, headers=auth_headers(member)).status_code == 409


def test_cannot_return_another_users_borrowing(client, user_factory, book_factory, auth_headers):
    member_a = user_factory(email="a@example.com")
    member_b = user_factory(email="b@example.com")
    book = book_factory()
    borrowing_id = client.post(
        f"/api/books/{book.id}/borrow", headers=auth_headers(member_a)
    ).json()["data"]["id"]
    response = client.post(
        f"/api/borrowings/{borrowing_id}/return", headers=auth_headers(member_b)
    )
    assert response.status_code == 403


def test_admin_can_return_another_users_borrowing(
    client, user_factory, book_factory, auth_headers
):
    member = user_factory()
    admin = user_factory(email="admin@example.com", role=UserRole.ADMIN)
    book = book_factory(total_copies=1)
    borrowing_id = client.post(
        f"/api/books/{book.id}/borrow", headers=auth_headers(member)
    ).json()["data"]["id"]
    response = client.post(
        f"/api/borrowings/{borrowing_id}/return", headers=auth_headers(admin)
    )
    assert response.status_code == 200


def test_my_borrowings_only_active(client, user_factory, book_factory, auth_headers):
    member = user_factory()
    book = book_factory()
    borrowing_id = client.post(
        f"/api/books/{book.id}/borrow", headers=auth_headers(member)
    ).json()["data"]["id"]

    active = client.get("/api/my/borrowings", headers=auth_headers(member)).json()["data"]
    assert len(active["items"]) == 1

    client.post(f"/api/borrowings/{borrowing_id}/return", headers=auth_headers(member))
    active = client.get("/api/my/borrowings", headers=auth_headers(member)).json()["data"]
    assert len(active["items"]) == 0
    assert active["meta"]["total"] == 0
    assert active["meta"]["page_size"] == 0

    history = client.get("/api/my/borrowings/history", headers=auth_headers(member)).json()["data"]
    assert len(history["items"]) == 1


def test_admin_can_list_all_borrowings(client, user_factory, book_factory, auth_headers):
    member = user_factory()
    admin = user_factory(email="admin@example.com", role=UserRole.ADMIN)
    book = book_factory()
    client.post(f"/api/books/{book.id}/borrow", headers=auth_headers(member))
    response = client.get("/api/borrowings", headers=auth_headers(admin))
    assert response.status_code == 200
    assert response.json()["data"]["meta"]["total"] == 1


def test_overdue_borrowing(client, user_factory, book_factory, auth_headers, db_session):
    member = user_factory()
    admin = user_factory(email="admin@example.com", role=UserRole.ADMIN)
    book = book_factory()
    borrowing_id = client.post(
        f"/api/books/{book.id}/borrow", headers=auth_headers(member)
    ).json()["data"]["id"]

    borrowing = db_session.get(Borrowing, borrowing_id)
    borrowing.due_at = datetime.now(timezone.utc) - timedelta(days=1)
    db_session.commit()

    overdue = client.get("/api/borrowings/overdue", headers=auth_headers(admin))
    body = overdue.json()["data"]
    assert overdue.status_code == 200
    assert body["meta"]["total"] == 1
    assert body["items"][0]["status"] == "OVERDUE"

    mine = client.get("/api/my/borrowings", headers=auth_headers(member)).json()["data"]
    assert mine["items"][0]["status"] == "OVERDUE"


def test_borrow_missing_book(client, user_factory, auth_headers):
    member = user_factory()
    assert client.post("/api/books/9999/borrow", headers=auth_headers(member)).status_code == 404


def test_borrow_requires_authentication(client, book_factory):
    book = book_factory()
    assert client.post(f"/api/books/{book.id}/borrow").status_code == 401