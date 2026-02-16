"""
Pytest configuration and shared fixtures for geology-engine tests.

SUPABASE_JWT_SECRET is set before any app import so auth uses a known test secret.
"""
import os
import time

import jwt
import pytest

# Set test JWT secret before app (and auth module) is imported
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret-do-not-use-in-production")

# Import app after env is set so auth module reads the test secret
from fastapi.testclient import TestClient

from app.main import app

TEST_JWT_SECRET = os.environ["SUPABASE_JWT_SECRET"]


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def valid_jwt():
    """A JWT valid for 1 hour, signed with TEST_JWT_SECRET (Supabase-style claims)."""
    now = int(time.time())
    payload = {
        "sub": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "email": "user@example.com",
        "role": "authenticated",
        "iat": now,
        "exp": now + 3600,
    }
    return jwt.encode(
        payload,
        TEST_JWT_SECRET,
        algorithm="HS256",
    )


@pytest.fixture
def expired_jwt():
    """A JWT that is already expired."""
    now = int(time.time())
    payload = {
        "sub": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "email": "user@example.com",
        "iat": now - 7200,
        "exp": now - 3600,
    }
    return jwt.encode(
        payload,
        TEST_JWT_SECRET,
        algorithm="HS256",
    )


@pytest.fixture
def tampered_jwt():
    """A JWT signed with a different secret (simulates tampering)."""
    now = int(time.time())
    payload = {
        "sub": "attacker-uuid",
        "email": "attacker@evil.com",
        "iat": now,
        "exp": now + 3600,
    }
    return jwt.encode(
        payload,
        "wrong-secret-at-least-32-bytes-long-for-hmac",
        algorithm="HS256",
    )
