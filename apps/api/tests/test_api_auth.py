"""
API integration tests for authentication endpoints.
"""

import pytest

from src.opsmesh.services.auth_service import create_refresh_token
from tests.conftest import make_auth_header


@pytest.mark.integration
class TestRegister:
    async def test_register_new_user(self, client):
        """New user can register and receive tokens."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@test.com",
                "name": "New User",
                "password": "secure-pass-123",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["access_token"] is not None
        assert data["refresh_token"] is not None
        assert data["user"]["email"] == "newuser@test.com"
        assert data["user"]["role"] == "viewer"

    async def test_rejects_duplicate_email(self, client, analyst_user):
        """Duplicate email should be rejected."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": analyst_user.email,
                "name": "Duplicate",
                "password": "secure-pass-123",
            },
        )
        assert response.status_code == 409

    async def test_rejects_short_password(self, client):
        """Password that's too short should be rejected."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "short@test.com",
                "name": "Short",
                "password": "123",
            },
        )
        assert response.status_code == 422

    async def test_rejects_invalid_email(self, client):
        """Invalid email format should be rejected."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "name": "Bad Email",
                "password": "secure-pass-123",
            },
        )
        assert response.status_code == 422


@pytest.mark.integration
class TestLogin:
    async def test_login_success(self, client, user_factory):
        """Valid credentials should return tokens."""
        await user_factory(email="login@test.com", password="correct-password")
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "login@test.com", "password": "correct-password"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] is not None
        assert data["user"]["email"] == "login@test.com"

    async def test_login_wrong_password(self, client, user_factory):
        """Wrong password should return 401."""
        await user_factory(email="wrong@test.com", password="correct")
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "wrong@test.com", "password": "incorrect"},
        )
        assert response.status_code == 401

    async def test_login_nonexistent_email(self, client):
        """Non-existent email should return 401."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@test.com", "password": "anything"},
        )
        assert response.status_code == 401


@pytest.mark.integration
class TestTokenRefresh:
    async def test_refresh_returns_new_tokens(self, client, user_factory):
        """Valid refresh token should return new tokens."""
        user = await user_factory(email="refresh@test.com")
        refresh_token = create_refresh_token(user_id=str(user.id))

        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] is not None
        assert data["refresh_token"] is not None

    async def test_rejects_invalid_refresh_token(self, client):
        """Invalid refresh token should return 401."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )
        assert response.status_code == 401


@pytest.mark.integration
class TestUserManagement:
    async def test_get_current_user(self, client, analyst_user):
        """Authenticated user can get their own profile."""
        headers = make_auth_header(analyst_user)
        response = await client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 200
        assert response.json()["email"] == analyst_user.email

    async def test_admin_can_list_users(self, client, admin_user):
        """Admin can list all users."""
        headers = make_auth_header(admin_user)
        response = await client.get("/api/v1/users", headers=headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_analyst_cannot_list_users(self, client, analyst_user):
        """Non-admin cannot list users."""
        headers = make_auth_header(analyst_user)
        response = await client.get("/api/v1/users", headers=headers)
        assert response.status_code == 403

    async def test_viewer_cannot_list_users(self, client, viewer_user):
        """Viewer cannot list users."""
        headers = make_auth_header(viewer_user)
        response = await client.get("/api/v1/users", headers=headers)
        assert response.status_code == 403
