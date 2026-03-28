"""
Tests for authentication and authorization.
"""

from src.opsmesh.services.auth_service import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_and_verify(self):
        password = "secure-password-123"
        hashed = hash_password(password)
        assert verify_password(password, hashed)

    def test_wrong_password_fails(self):
        hashed = hash_password("correct-password")
        assert not verify_password("wrong-password", hashed)

    def test_hash_is_not_plaintext(self):
        password = "my-password"
        hashed = hash_password(password)
        assert hashed != password

    def test_different_hashes_for_same_password(self):
        password = "same-password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2  # bcrypt uses random salt


class TestJWTTokens:
    def test_create_and_decode_access_token(self):
        token = create_access_token(
            user_id="user-123", email="test@test.com", role="admin"
        )
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["email"] == "test@test.com"
        assert payload["role"] == "admin"
        assert payload["type"] == "access"

    def test_create_and_decode_refresh_token(self):
        token = create_refresh_token(user_id="user-123")
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["type"] == "refresh"

    def test_invalid_token_returns_none(self):
        result = decode_token("invalid-token-string")
        assert result is None

    def test_token_contains_expiration(self):
        token = create_access_token(
            user_id="user-123", email="test@test.com", role="viewer"
        )
        payload = decode_token(token)
        assert "exp" in payload

    def test_different_roles_encoded(self):
        for role in ["admin", "analyst", "viewer"]:
            token = create_access_token(
                user_id="user-123", email="test@test.com", role=role
            )
            payload = decode_token(token)
            assert payload["role"] == role


class TestRoles:
    def test_role_hierarchy(self):
        """Verify role names match expected values."""
        from src.opsmesh.models.user import UserRole

        assert UserRole.ADMIN.value == "admin"
        assert UserRole.ANALYST.value == "analyst"
        assert UserRole.VIEWER.value == "viewer"

    def test_role_is_string_enum(self):
        """UserRole should be a StrEnum."""
        from src.opsmesh.models.user import UserRole

        assert UserRole.ADMIN == "admin"
        assert str(UserRole.ADMIN) == "admin"

    def test_all_roles_defined(self):
        """All three roles should be defined."""
        from src.opsmesh.models.user import UserRole

        roles = list(UserRole)
        assert len(roles) == 3
        role_values = [r.value for r in roles]
        assert "admin" in role_values
        assert "analyst" in role_values
        assert "viewer" in role_values


class TestTokenTypes:
    def test_access_token_type(self):
        token = create_access_token(
            user_id="user-123", email="test@test.com", role="admin"
        )
        payload = decode_token(token)
        assert payload["type"] == "access"

    def test_refresh_token_type(self):
        token = create_refresh_token(user_id="user-123")
        payload = decode_token(token)
        assert payload["type"] == "refresh"

    def test_access_token_has_email_and_role(self):
        token = create_access_token(
            user_id="user-123", email="test@test.com", role="analyst"
        )
        payload = decode_token(token)
        assert "email" in payload
        assert "role" in payload

    def test_refresh_token_minimal_payload(self):
        token = create_refresh_token(user_id="user-123")
        payload = decode_token(token)
        assert payload["sub"] == "user-123"
        assert payload["type"] == "refresh"
        # Refresh token should not have email/role
        assert "email" not in payload
        assert "role" not in payload
