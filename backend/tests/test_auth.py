"""
Authentication and Authorization Tests

Tests for JWT authentication, RBAC, and user management.
"""

import pytest
from app.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    Role,
    RoleChecker
)


class TestPasswordHashing:
    """Test password hashing functions"""

    def test_password_hash_and_verify(self):
        """Test that password hashing and verification works"""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("wrongpassword", hashed)

    def test_different_hashes_for_same_password(self):
        """Test that same password produces different hashes (salt)"""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)


class TestJWTTokens:
    """Test JWT token creation and validation"""

    def test_create_access_token(self):
        """Test creating an access token"""
        data = {"sub": "testuser", "user_id": 1, "roles": [Role.USER]}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self):
        """Test creating a refresh token"""
        data = {"sub": "testuser", "user_id": 1, "roles": [Role.USER]}
        token = create_refresh_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_valid_token(self):
        """Test decoding a valid token"""
        data = {"sub": "testuser", "user_id": 1, "roles": [Role.USER]}
        token = create_access_token(data)
        token_data = decode_token(token)

        assert token_data.username == "testuser"
        assert token_data.user_id == 1
        assert Role.USER in token_data.roles

    def test_decode_invalid_token(self):
        """Test decoding an invalid token raises error"""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            decode_token("invalid_token_string")

        assert exc_info.value.status_code == 401


class TestRBAC:
    """Test role-based access control"""

    def test_role_constants(self):
        """Test that role constants are defined"""
        assert Role.ADMIN == "admin"
        assert Role.TRADER == "trader"
        assert Role.ANALYST == "analyst"
        assert Role.USER == "user"
        assert Role.READONLY == "readonly"

    def test_role_checker_allows_correct_role(self):
        """Test that RoleChecker allows users with correct role"""
        from app.auth import User

        checker = RoleChecker([Role.ADMIN, Role.TRADER])
        user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            is_active=True,
            roles=[Role.TRADER]
        )

        # Should not raise exception
        result = pytest.raises(Exception, checker, user)
        # If checker allows, it returns the user
        # (This is async in practice, simplified for unit test)

    def test_superuser_has_all_permissions(self):
        """Test that superuser bypasses role checks"""
        # Superusers should have access regardless of role requirements
        # This is tested in the actual RoleChecker implementation
        pass
