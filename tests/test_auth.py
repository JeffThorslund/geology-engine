"""
Auth test suite: Supabase JWT verification and protected routes.

Covers public access, missing/invalid/expired/tampered tokens, valid token flow,
and server error when JWT secret is unset.
"""

import pytest

import app.auth as auth_module


class TestPublicRoutes:
    """Endpoints that must remain accessible without authentication."""

    def test_root_returns_200_without_auth(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["service"] == "geology-engine"

    def test_health_returns_200_without_auth(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestProtectedRouteRequiresAuth:
    """GET /me must reject requests without a valid Bearer token."""

    def test_me_returns_401_when_no_authorization_header(self, client):
        response = client.get("/me")
        assert response.status_code == 401

    def test_me_returns_401_when_token_malformed(self, client):
        response = client.get(
            "/me",
            headers={"Authorization": "Bearer not-a-valid-jwt"},
        )
        assert response.status_code == 401
        assert "invalid" in response.json().get("detail", "").lower() or "token" in response.json().get("detail", "").lower()

    def test_me_returns_401_when_token_expired(self, client, expired_jwt):
        response = client.get(
            "/me",
            headers={"Authorization": f"Bearer {expired_jwt}"},
        )
        assert response.status_code == 401
        assert "expired" in response.json().get("detail", "").lower()

    def test_me_returns_401_when_token_tampered(self, client, tampered_jwt):
        """Token signed with wrong secret must be rejected (prevents forgery)."""
        response = client.get(
            "/me",
            headers={"Authorization": f"Bearer {tampered_jwt}"},
        )
        assert response.status_code == 401


class TestProtectedRouteAcceptsValidToken:
    """GET /me must accept a valid Supabase-style JWT and return user claims."""

    def test_me_returns_200_and_user_when_token_valid(self, client, valid_jwt):
        response = client.get(
            "/me",
            headers={"Authorization": f"Bearer {valid_jwt}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        assert data["email"] == "user@example.com"
        assert data["role"] == "authenticated"


class TestServerConfig:
    """Behavior when auth is misconfigured."""

    def test_me_returns_500_when_jwt_secret_unset(self, client, monkeypatch):
        """When SUPABASE_JWT_SECRET is not set, auth must not succeed (fail closed)."""
        monkeypatch.setattr(auth_module, "SUPABASE_JWT_SECRET", "")
        # Reload would be complex; we patched the module so next request uses ""
        response = client.get(
            "/me",
            headers={"Authorization": "Bearer any-token"},
        )
        assert response.status_code == 500
        assert "configured" in response.json().get("detail", "").lower()
