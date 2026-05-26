from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import verify_password
from app.repositories.user_repository import create_user, get_user_by_email
from app.schemas.user import UserCreate
from app.utils import generate_password_reset_token


def test_register_and_login(client: TestClient) -> None:
    email = "newuser@example.com"
    password = "testpassword123"
    response = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"email": email, "full_name": "New User", "password": password},
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["email"] == email

    login_response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": email, "password": password},
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data


def test_forgot_password_returns_generic_message(client: TestClient, db: Session) -> None:
    user = create_user(
        db,
        UserCreate(email="forgot@example.com", full_name="Forgot User", password="password123"),
    )

    with patch("app.api.v1.endpoints.auth.send_email") as send_email_mock:
        response = client.post(
            f"{settings.API_V1_STR}/auth/forgot-password",
            json={"email": user.email},
        )

    assert response.status_code == 200
    assert response.json()["message"] == "If that email is registered, we sent a password recovery link"
    send_email_mock.assert_called_once()


def test_reset_password_updates_user_password(client: TestClient, db: Session) -> None:
    email = "reset@example.com"
    password = "initialPassword123"
    new_password = "newPassword456"
    user = create_user(
        db,
        UserCreate(email=email, full_name="Reset User", password=password),
    )

    token = generate_password_reset_token(user.email)
    response = client.post(
        f"{settings.API_V1_STR}/auth/reset-password",
        json={"token": token, "new_password": new_password},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Password updated successfully"

    refreshed_user = get_user_by_email(db, email)
    assert refreshed_user is not None
    assert verify_password(new_password, refreshed_user.hashed_password)


def test_reset_password_rejects_invalid_token(client: TestClient) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/auth/reset-password",
        json={"token": "invalid-token", "new_password": "password123"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid token"
