import pytest


def _register(client, email="alice@example.com", password="Password@123", name="Alice"):
    return client.post(
        "/api/auth/register",
        json={"name": name, "email": email, "password": password},
    )


def _login(client, email="alice@example.com", password="Password@123"):
    return client.post(
        "/api/auth/login", json={"email": email, "password": password}
    )


def test_register_success(client):
    response = _register(client)
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["email"] == "alice@example.com"
    assert body["data"]["role"] == "MEMBER"
    assert "password_hash" not in body["data"]


def test_register_duplicate_email(client):
    assert _register(client).status_code == 201
    assert _register(client).status_code == 409


def test_register_weak_password(client):
    assert _register(client, password="short").status_code == 422


def test_register_invalid_email(client):
    assert _register(client, email="not-an-email").status_code == 422


def test_login_success(client):
    _register(client)
    response = _login(client)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["access_token"]
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "alice@example.com"


def test_login_wrong_password(client):
    _register(client)
    response = _login(client, password="WrongPass@123")
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False


def test_login_unknown_email(client):
    response = _login(client, email="nobody@example.com")
    assert response.status_code == 401


def test_get_me(client):
    _register(client)
    token = _login(client).json()["data"]["access_token"]
    response = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["data"]["email"] == "alice@example.com"


def test_get_me_invalid_token(client):
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer not.a.jwt"})
    assert response.status_code == 401


def test_get_me_missing_token(client):
    assert client.get("/api/auth/me").status_code == 401