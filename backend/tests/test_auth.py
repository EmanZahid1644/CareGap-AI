
import uuid
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from backend.app.core.security import (
    create_access_token,
    decode_access_token,
)
from backend.app.main import app
from backend.app.models.identity import User


client = TestClient(app)


@pytest.fixture(autouse=True)
def use_isolated_database(isolated_db):
    """Automatically isolate each authentication test."""
    yield


# ============================================================
# REGISTRATION TESTS
# ============================================================

def test_register_user_success(isolated_db):
    email = f"register-{uuid.uuid4().hex}@example.com"
    password = "SecureTestPassword123!"

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Test Registration User",
            "password": password,
            "account_type": "personal",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == email
    assert data["full_name"] == "Test Registration User"
    assert data["account_type"] == "personal"
    assert "id" in data
    assert "password" not in data
    assert "password_hash" not in data

    # Read using the same isolated database transaction.
    user = isolated_db.get(User, uuid.UUID(data["id"]))

    assert user is not None
    assert user.password_hash != password
    assert user.password_hash.startswith("$argon2")


def test_register_duplicate_email():
    email = f"duplicate-{uuid.uuid4().hex}@example.com"

    payload = {
        "email": email,
        "full_name": "Duplicate Test User",
        "password": "SecureTestPassword123!",
        "account_type": "personal",
    }

    first_response = client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    assert second_response.status_code == 409


def test_register_invalid_email():
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "full_name": "Invalid Email User",
            "password": "SecureTestPassword123!",
            "account_type": "personal",
        },
    )

    assert response.status_code == 422


def test_register_short_password():
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"short-{uuid.uuid4().hex}@example.com",
            "full_name": "Short Password User",
            "password": "12345",
            "account_type": "personal",
        },
    )

    assert response.status_code == 422


# ============================================================
# LOGIN TESTS
# ============================================================

def test_login_success():
    email = f"login-{uuid.uuid4().hex}@example.com"
    password = "SecureLoginPassword123!"

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Login Test User",
            "password": password,
            "account_type": "personal",
        },
    )

    assert register_response.status_code == 201

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 20

    payload = decode_access_token(data["access_token"])

    assert payload["sub"] == register_response.json()["id"]
    assert payload["type"] == "access"


def test_login_wrong_password():
    email = f"wrong-{uuid.uuid4().hex}@example.com"

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Wrong Password Test",
            "password": "CorrectPassword123!",
            "account_type": "personal",
        },
    )

    assert register_response.status_code == 201

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "IncorrectPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Invalid email or password."
    )


def test_login_nonexistent_user():
    email = f"missing-{uuid.uuid4().hex}@example.com"

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "SomePassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Invalid email or password."
    )


# ============================================================
# JWT-PROTECTED PROFILE TESTS
# ============================================================

def test_me_without_token():
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Invalid or missing authentication token."
    )


def test_me_with_invalid_token():
    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": "Bearer invalid.jwt.token",
        },
    )

    assert response.status_code == 401


def test_me_with_valid_token():
    email = f"profile-{uuid.uuid4().hex}@example.com"
    password = "SecureProfilePassword123!"

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Profile Test User",
            "password": password,
            "account_type": "personal",
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == register_response.json()["id"]
    assert data["email"] == email
    assert data["full_name"] == "Profile Test User"
    assert data["account_type"] == "personal"
    assert "password" not in data
    assert "password_hash" not in data


def test_me_with_expired_token():
    expired_token = create_access_token(
        subject=str(uuid.uuid4()),
        expires_delta=timedelta(seconds=-10),
    )

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {expired_token}",
        },
    )

    assert response.status_code == 401
