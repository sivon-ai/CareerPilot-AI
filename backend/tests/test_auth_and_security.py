from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_register_and_login_roundtrip() -> None:
    response = client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "StrongPass1!", "full_name": "Test User"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["user"]["email"] == "user@example.com"
    assert "password" not in payload["user"]

    login = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "StrongPass1!"},
    )
    assert login.status_code == 200, login.text
    body = login.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_duplicate_email_is_rejected() -> None:
    response = client.post(
        "/auth/register",
        json={"email": "dup@example.com", "password": "StrongPass1!", "full_name": "Dup"},
    )
    assert response.status_code == 200

    repeat = client.post(
        "/auth/register",
        json={"email": "dup@example.com", "password": "StrongPass1!", "full_name": "Dup2"},
    )
    assert repeat.status_code == 409


def test_protected_document_route_requires_auth() -> None:
    response = client.get("/documents/does-not-exist")
    assert response.status_code in {401, 404}


def test_weak_password_is_rejected() -> None:
    response = client.post(
        "/auth/register",
        json={"email": "weak@example.com", "password": "short", "full_name": "Weak"},
    )
    assert response.status_code == 422
