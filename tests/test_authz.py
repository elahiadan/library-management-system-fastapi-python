from app.models.user import UserRole


def test_unauthenticated_gets_401(client):
    assert client.get("/api/books").status_code == 401
    assert client.get("/api/authors").status_code == 401
    assert client.get("/api/users").status_code == 401


def test_member_cannot_access_admin_endpoint(client, user_factory, author_factory, auth_headers):
    member = user_factory()
    author = author_factory()
    response = client.post(
        "/api/books",
        headers=auth_headers(member),
        json={
            "title": "Hacker Book",
            "isbn": "9781234567890",
            "published_year": 2020,
            "total_copies": 2,
            "author_id": author.id,
        },
    )
    assert response.status_code == 403
    assert response.json()["success"] is False


def test_admin_can_access_admin_endpoint(client, user_factory, author_factory, auth_headers):
    admin = user_factory(email="admin@example.com", role=UserRole.ADMIN)
    author = author_factory()
    response = client.post(
        "/api/books",
        headers=auth_headers(admin),
        json={
            "title": "Admin Book",
            "isbn": "9781234567890",
            "published_year": 2020,
            "total_copies": 2,
            "author_id": author.id,
        },
    )
    assert response.status_code == 201


def test_member_cannot_list_users(client, user_factory, auth_headers):
    member = user_factory()
    assert client.get("/api/users", headers=auth_headers(member)).status_code == 403


def test_admin_can_list_users(client, user_factory, auth_headers):
    admin = user_factory(email="admin@example.com", role=UserRole.ADMIN)
    response = client.get("/api/users", headers=auth_headers(admin))
    assert response.status_code == 200
    assert response.json()["data"]["meta"]["total"] >= 1


def test_admin_cannot_borrow_books(client, user_factory, book_factory, auth_headers):
    admin = user_factory(email="admin@example.com", role=UserRole.ADMIN)
    book = book_factory()
    response = client.post(
        f"/api/books/{book.id}/borrow", headers=auth_headers(admin)
    )
    assert response.status_code == 403