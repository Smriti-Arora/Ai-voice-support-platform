
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def create_test_user():
    email = f"auth_test_{uuid4().hex[:10]}@example.com"
    password = "TestPassword123!"

    response = client.post(
        "/auth/register",
        json={
            "full_name": "Auth Test User",
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 201
    return email, password



def test_register_user():
    email, password = create_test_user()

    response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )

    assert response.status_code == 200
    assert response.json()["access_token"]



def test_register_duplicate_email():
    email, password = create_test_user()

    response = client.post(
        "/auth/register",
        json={
            "full_name": "Duplicate User",
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 409


def test_login_success():
    email, password = create_test_user()

    response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]


def test_login_wrong_password():
    email, _ = create_test_user()

    response = client.post(
        "/auth/login",
        json={"email": email, "password": "WrongPassword123!"},
    )

    assert response.status_code == 401


def test_auth_me_without_token():
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_auth_me_with_valid_token():
    email, password = create_test_user()

    login_response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == email
    assert response.json()["full_name"] == "Auth Test User"
    assert "hashed_password" not in response.json()


def test_auth_me_with_invalid_token():
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401


def test_auth_me_with_inactive_user():
    email, password = create_test_user()

    # Login first to obtain a valid token.
    login_response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Deactivate this user in the test database.
    from app.db.session import SessionLocal
    from app.models.user import User

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        assert user is not None
        user.is_active = False
        db.commit()
    finally:
        db.close()

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401

