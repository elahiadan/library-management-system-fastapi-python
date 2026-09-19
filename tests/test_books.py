from sqlalchemy import select

from app.models import Author
from app.models.user import UserRole


def _admin_headers(client, user_factory, auth_headers):
    admin = user_factory(email="admin@example.com", role=UserRole.ADMIN)
    return auth_headers(admin)


def _book_payload(author_id, isbn="9780134685634", title="Test Book", total_copies=2):
    return {
        "title": title,
        "isbn": isbn,
        "description": "Description",
        "published_year": 2020,
        "total_copies": total_copies,
        "author_id": author_id,
    }


def test_create_book(client, user_factory, author_factory, auth_headers, db_session):
    headers = _admin_headers(client, user_factory, auth_headers)
    author = author_factory()
    response = client.post("/api/books", headers=headers, json=_book_payload(author.id))
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["title"] == "Test Book"
    assert data["available_copies"] == 2
    assert data["author"]["name"] == author.name


def test_create_book_invalid_isbn(client, user_factory, author_factory, auth_headers):
    headers = _admin_headers(client, user_factory, auth_headers)
    author = author_factory()
    response = client.post(
        "/api/books", headers=headers, json=_book_payload(author.id, isbn="12345")
    )
    assert response.status_code == 422


def test_create_book_duplicate_isbn(client, user_factory, author_factory, auth_headers):
    headers = _admin_headers(client, user_factory, auth_headers)
    author = author_factory()
    payload = _book_payload(author.id)
    assert client.post("/api/books", headers=headers, json=payload).status_code == 201
    assert client.post("/api/books", headers=headers, json=payload).status_code == 409


def test_create_book_negative_copies(client, user_factory, author_factory, auth_headers):
    headers = _admin_headers(client, user_factory, auth_headers)
    author = author_factory()
    payload = _book_payload(author.id, total_copies=-1)
    assert client.post("/api/books", headers=headers, json=payload).status_code == 422


def test_create_book_author_not_found(client, user_factory, auth_headers):
    headers = _admin_headers(client, user_factory, auth_headers)
    payload = _book_payload(author_id=9999)
    assert client.post("/api/books", headers=headers, json=payload).status_code == 404


def test_get_book(client, user_factory, book_factory, auth_headers):
    book = book_factory()
    member = user_factory()
    response = client.get(f"/api/books/{book.id}", headers=auth_headers(member))
    assert response.status_code == 200
    assert response.json()["data"]["title"] == book.title


def test_get_book_not_found(client, user_factory, auth_headers):
    member = user_factory()
    assert client.get("/api/books/9999", headers=auth_headers(member)).status_code == 404


def test_update_book(client, user_factory, author_factory, book_factory, auth_headers):
    book = book_factory()
    headers = _admin_headers(client, user_factory, auth_headers)
    response = client.put(
        f"/api/books/{book.id}", headers=headers, json={"title": "Updated Title"}
    )
    assert response.status_code == 200
    assert response.json()["data"]["title"] == "Updated Title"


def test_update_book_increase_total_copies(client, user_factory, book_factory, auth_headers):
    book = book_factory(total_copies=2)
    headers = _admin_headers(client, user_factory, auth_headers)
    response = client.put(
        f"/api/books/{book.id}", headers=headers, json={"total_copies": 5}
    )
    data = response.json()["data"]
    assert data["total_copies"] == 5
    assert data["available_copies"] == 5


def test_update_book_reduce_below_available_conflict(
    client, user_factory, book_factory, auth_headers, db_session
):
    book = book_factory(total_copies=5)
    headers = _admin_headers(client, user_factory, auth_headers)
    book_row = db_session.get(type(book), book.id)
    book_row.available_copies = 2
    db_session.commit()
    response = client.put(
        f"/api/books/{book.id}", headers=headers, json={"total_copies": 1}
    )
    assert response.status_code == 400


def test_delete_book(client, user_factory, book_factory, auth_headers):
    book = book_factory()
    headers = _admin_headers(client, user_factory, auth_headers)
    assert client.delete(f"/api/books/{book.id}", headers=headers).status_code == 204


def test_delete_book_with_borrowing_conflict(
    client, user_factory, book_factory, borrowing_factory, auth_headers
):
    book = book_factory()
    member = user_factory()
    borrowing_factory(user=member, book=book)
    headers = _admin_headers(client, user_factory, auth_headers)
    assert client.delete(f"/api/books/{book.id}", headers=headers).status_code == 409


def test_search_books(client, user_factory, book_factory, auth_headers):
    book_factory(title="Learning Python")
    book_factory(title="Learning Java")
    member = user_factory()
    response = client.get("/api/books?search=python", headers=auth_headers(member))
    body = response.json()["data"]
    assert body["meta"]["total"] == 1
    assert body["items"][0]["title"] == "Learning Python"


def test_filter_books_by_author(client, user_factory, author_factory, book_factory, auth_headers):
    author1 = author_factory(name="Author One")
    author2 = author_factory(name="Author Two")
    book_factory(title="Book A", author=author1)
    book_factory(title="Book B", author=author2)
    member = user_factory()
    response = client.get(f"/api/books?author_id={author1.id}", headers=auth_headers(member))
    body = response.json()["data"]
    assert body["meta"]["total"] == 1
    assert body["items"][0]["title"] == "Book A"


def test_filter_books_available(client, user_factory, book_factory, auth_headers):
    book_factory(title="In Stock", total_copies=2)
    book_factory(title="Out of Stock", total_copies=0)
    member = user_factory()
    response = client.get("/api/books?available=true", headers=auth_headers(member))
    body = response.json()["data"]
    assert body["meta"]["total"] == 1
    assert body["items"][0]["title"] == "In Stock"


def test_books_pagination(client, user_factory, book_factory, auth_headers):
    for i in range(5):
        book_factory(title=f"Book {i}")
    member = user_factory()
    response = client.get("/api/books?page=1&page_size=2", headers=auth_headers(member))
    body = response.json()["data"]
    assert len(body["items"]) == 2
    assert body["meta"]["total"] == 5
    assert body["meta"]["total_pages"] == 3


def test_invalid_pagination_params(client, user_factory, auth_headers):
    member = user_factory()
    response = client.get("/api/books?page=0", headers=auth_headers(member))
    assert response.status_code == 422