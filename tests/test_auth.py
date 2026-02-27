"""
Auth test suite: API key verification and protected routes.

Covers public access, missing/wrong key, valid key, and server misconfiguration.
"""

import pytest


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


class TestAuthenticatedHealthCheck:
    """Authenticated health check endpoint tests."""

    def test_health_auth_returns_401_without_key(self, client):
        response = client.get("/health/auth")
        assert response.status_code in (401, 403)

    def test_health_auth_returns_401_with_wrong_key(self, client):
        response = client.get(
            "/health/auth",
            headers={"Authorization": "Bearer wrong-key"},
        )
        assert response.status_code == 401

    def test_health_auth_returns_200_with_valid_key(self, client, auth_headers):
        response = client.get("/health/auth", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "geology-engine"


class TestProtectedRouteRequiresAuth:
    """Protected endpoints must reject requests without a valid API key."""

    def test_coefficients_returns_401_without_key(self, client):
        response = client.post("/rbf/coefficients", json={"intervals": [], "fitting_accuracy": 0.01})
        assert response.status_code in (401, 403)

    def test_coefficients_returns_401_with_wrong_key(self, client):
        response = client.post(
            "/rbf/coefficients",
            json={"intervals": [], "fitting_accuracy": 0.01},
            headers={"Authorization": "Bearer wrong-key"},
        )
        assert response.status_code == 401

    def test_evaluate_returns_401_without_key(self, client):
        response = client.post(
            "/rbf/evaluate",
            json={"intervals": [], "query_points": [], "fitting_accuracy": 0.01},
        )
        assert response.status_code in (401, 403)


class TestServerConfig:
    """Behavior when auth is misconfigured."""

    def test_returns_500_when_api_key_unset(self, client, monkeypatch):
        """When GEOLOGY_ENGINE_API_KEY is empty, auth must fail closed."""
        mock_settings = type("MockSettings", (), {"get_api_key_str": lambda self: ""})()
        monkeypatch.setattr("app.auth.get_settings", lambda: mock_settings)
        response = client.get(
            "/health/auth",
            headers={"Authorization": "Bearer any-key"},
        )
        assert response.status_code == 500
        assert "configured" in response.json().get("detail", "").lower()
