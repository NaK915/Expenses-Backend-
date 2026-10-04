import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def register(name: str, email: str) -> dict:
    response = client.post(
        "/auth/register",
        json={"name": name, "email": email, "password": "secret123"},
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.mongo
def test_authenticated_group_transaction_flow():
    suffix = uuid.uuid4().hex
    alice = register("Alice", f"alice-{suffix}@example.com")
    bob = register("Bob", f"bob-{suffix}@example.com")
    alice_headers = {"Authorization": f"Bearer {alice['access_token']}"}

    group_response = client.post(
        "/groups",
        headers=alice_headers,
        json={"name": "Trip to Goa", "description": "Vacation expenses"},
    )
    assert group_response.status_code == 201
    group = group_response.json()

    member_response = client.post(
        f"/groups/{group['id']}/members",
        headers=alice_headers,
        json={"email": bob["user"]["email"]},
    )
    assert member_response.status_code == 201

    transaction_response = client.post(
        f"/groups/{group['id']}/transactions",
        headers=alice_headers,
        json={
            "title": "Hotel",
            "amount": 1200,
            "split_between": [alice["user"]["id"], bob["user"]["id"]],
            "category": "travel",
        },
    )
    assert transaction_response.status_code == 201
    transaction = transaction_response.json()
    assert transaction["transaction_type"] == "expense"

    reimbursement = client.post(
        f"/groups/{group['id']}/transactions",
        headers={"Authorization": f"Bearer {bob['access_token']}"},
        json={
            "title": "Hotel reimbursement",
            "amount": 600,
            "transaction_type": "reimbursement",
            "to_user_id": alice["user"]["id"],
        },
    )
    assert reimbursement.status_code == 201

    edit_response = client.patch(
        f"/transactions/{transaction['id']}",
        headers=alice_headers,
        json={"amount": 1250},
    )
    assert edit_response.status_code == 200
    assert edit_response.json()["amount"] == 1250

    balances_response = client.get(f"/groups/{group['id']}/balances", headers=alice_headers)
    assert balances_response.status_code == 200
    assert len(balances_response.json()["members"]) == 2

    delete_response = client.delete(f"/transactions/{transaction['id']}", headers=alice_headers)
    assert delete_response.status_code == 204


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
