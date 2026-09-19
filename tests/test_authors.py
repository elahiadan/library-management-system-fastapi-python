from sqlalchemy import select

from app.models import User
from app.models.user import UserRole


def _admin_headers(client, user_factory, auth_headers):
    admin = user_factory(email="admin@example.com", role=UserRole.ADMIN)
    return auth_headers(admin)


def test_create_author(client, user_factory, auth_headers):
    headers = _admin_headers(client, user_factory, auth_headers)
    response = client.post(
        "/api/authors",
        headers=headers,
        json={"name": "Jane Austen", "bio": "Novelist"},
    )
    assert response.status_code == 201
    assert response.json()["data"]["name"] == "Jane Austen"


def test_member_cannot_create_author(client, user_factory, auth_headers):
    member = user_factory()
    response = client.post(
        "/api/authors", headers=auth_headers(member), json={"name": "X"}
    )
    assert response.status_code == 403


def test_list_authors(client, user_factory, author_factory, auth_headers):
    author_factory(name="Leo Tolstoy")
    author_factory(name="Fyodor Dostoevsky")
    member = user_factory()
    response = client.get("/api/authors", headers=auth_headers(member))
    assert response.status_code == 200
    assert response.json()["data"]["meta"]["total"] == 2


def test_get_author(client, user_factory, author_factory, auth_headers):
    author = author_factory(name="Leo Tolstoy")
    member = user_factory()
    response = client.get(
        f"/api/authors/{author.id}", headers=auth_headers(member)
    )
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Leo Tolstoy"


def test_get_author_not_found(client, user_factory, auth_headers):
    member = user_factory()
    assert client.get("/api/authors/9999", headers=auth_headers(member)).status_code == 404


def test_update_author(client, user_factory, author_factory, auth_headers):
    author = author_factory(name="Old Name")
    headers = _admin_headers(client, user_factory, auth_headers)
    response = client.put(
        f"/api/authors/{author.id}", headers=headers, json={"name": "New Name"}
    )
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "New Name"


def test_delete_author(client, user_factory, author_factory, auth_headers):
    author = author_factory()
    headers = _admin_headers(client, user_factory, auth_headers)
    assert client.delete(f"/api/authors/{author.id}", headers=headers).status_code == 204


def test_delete_author_with_books_conflict(client, user_factory, author_factory, book_factory, auth_headers):
    author = author_factory()
    book_factory(author=author)
    headers = _admin_headers(client, user_factory, auth_headers)
    response = client.delete(f"/api/authors/{author.id}", headers=headers)
    assert response.status_code == 409


def test_author_pagination(client, user_factory, author_factory, auth_headers):
    for i in range(5):
        author_factory(name=f"Author {i}")
    member = user_factory()
    response = client.get("/api/authors?page=1&page_size=2", headers=auth_headers(member))
    body = response.json()["data"]
    assert len(body["items"]) == 2
    assert body["meta"]["total"] == 5
    assert body["meta"]["total_pages"] == 3