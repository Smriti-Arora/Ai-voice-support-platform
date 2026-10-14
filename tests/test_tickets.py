from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_ticket():
    response = client.post(
        "/tickets",
        json={
            "customer_name": "Test Customer",
            "customer_email": "test.customer@example.com",
            "subject": "Test support ticket",
            "description": "This is an automated test ticket.",
            "priority": "high",
        },
    )

    assert response.status_code == 201

    data = response.json()
    assert data["customer_name"] == "Test Customer"
    assert data["customer_email"] == "test.customer@example.com"
    assert data["subject"] == "Test support ticket"
    assert data["status"] == "open"
    assert data["priority"] == "high"
    assert "id" in data


def test_create_ticket_invalid_priority():
    response = client.post(
        "/tickets",
        json={
            "customer_name": "Test Customer",
            "customer_email": "test.customer@example.com",
            "subject": "Invalid priority test",
            "description": "Testing input validation.",
            "priority": "super-urgent",
        },
    )

    assert response.status_code == 422


def test_get_nonexistent_ticket():
    response = client.get("/tickets/999999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Support ticket not found"

def test_list_tickets():
    response = client.get("/tickets")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_update_ticket():
    create_response = client.post(
        "/tickets",
        json={
            "customer_name": "Update Test Customer",
            "customer_email": "update.test@example.com",
            "subject": "Ticket update test",
            "description": "Testing ticket status update.",
            "priority": "medium",
        },
    )

    assert create_response.status_code == 201
    ticket_id = create_response.json()["id"]

    update_response = client.patch(
        f"/tickets/{ticket_id}",
        json={"status": "in_progress"},
    )

    assert update_response.status_code == 200
    assert update_response.json()["status"] == "in_progress"
    assert update_response.json()["priority"] == "medium"


def test_delete_ticket():
    create_response = client.post(
        "/tickets",
        json={
            "customer_name": "Delete Test Customer",
            "customer_email": "delete.test@example.com",
            "subject": "Ticket deletion test",
            "description": "Testing ticket deletion.",
            "priority": "low",
        },
    )

    assert create_response.status_code == 201
    ticket_id = create_response.json()["id"]

    delete_response = client.delete(f"/tickets/{ticket_id}")

    assert delete_response.status_code == 200
    assert delete_response.json()["ticket_id"] == ticket_id

    get_response = client.get(f"/tickets/{ticket_id}")
    assert get_response.status_code == 404

