import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
pytestmark = pytest.mark.mongo


def test_user_registration_login_and_profile():
    email = f"user-{uuid.uuid4().hex}@example.com"
    register = client.post(
        "/auth/register",
        json={"name": "Bob", "email": email, "password": "secret123"},
    )
    assert register.status_code == 201
    assert "password_hash" not in register.json()["user"]

    login = client.post(
        "/auth/login",
        json={"email": email, "password": "secret123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    profile = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert profile.status_code == 200
    assert profile.json()["email"] == email
    assert "password_hash" not in profile.json()
