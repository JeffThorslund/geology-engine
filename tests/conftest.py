"""
Pytest configuration and shared fixtures for geology-engine tests.

GEOLOGY_ENGINE_API_KEY is set before any app import so auth uses a known test key.
"""
import os

import pytest

# Set test API key before app is imported
os.environ.setdefault("GEOLOGY_ENGINE_API_KEY", "test-api-key-do-not-use-in-production")

from fastapi.testclient import TestClient

from app.main import app

TEST_API_KEY = os.environ["GEOLOGY_ENGINE_API_KEY"]


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Authorization headers with the valid test API key."""
    return {"Authorization": f"Bearer {TEST_API_KEY}"}
