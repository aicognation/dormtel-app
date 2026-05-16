import pytest
from decimal import Decimal

pytestmark = pytest.mark.asyncio


async def test_create_inquiry_sets_status_new(async_client, db_session):
    payload = {
        "source": "facebook",
        "content": "Hello, I am interested in a room",
        "external_id": "fb-123",
    }
    response = await async_client.post("/api/v1/inquiries/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "new"
    assert data["source"] == "facebook"
    assert "id" in data
    assert data["lead_score"] is not None


async def test_high_sentiment_triggers_positive_auto_response(async_client, db_session):
    payload = {
        "source": "instagram",
        "content": "I love your place! It looks amazing and perfect!",
        "external_id": "ig-456",
    }
    create_resp = await async_client.post("/api/v1/inquiries/", json=payload)
    assert create_resp.status_code == 201
    data = create_resp.json()
    assert Decimal(data["sentiment_score"]) >= Decimal("0.85")
    inquiry_id = data["id"]

    respond_resp = await async_client.post(f"/api/v1/inquiries/{inquiry_id}/respond")
    assert respond_resp.status_code == 200
    resp_data = respond_resp.json()
    assert resp_data["status"] == "responded"
    assert "schedule a tour" in resp_data["auto_response"].lower()


async def test_discount_keywords_escalate_to_admin_checkpoint(async_client, db_session):
    payload = {
        "source": "phone",
        "content": "Can you give me a discount? I want to negotiate the price.",
        "external_id": "ph-789",
    }
    create_resp = await async_client.post("/api/v1/inquiries/", json=payload)
    assert create_resp.status_code == 201
    inquiry_id = create_resp.json()["id"]

    escalate_resp = await async_client.post(f"/api/v1/inquiries/{inquiry_id}/escalate")
    assert escalate_resp.status_code == 200
    data = escalate_resp.json()
    assert data["status"] == "escalated"
    assert data["checkpoint_id"].startswith("CP-01")
    assert data["stage"] == "Admin Review"


async def test_angry_sentiment_escalates_to_manager_checkpoint(async_client, db_session):
    payload = {
        "source": "facebook",
        "content": "I am very angry and frustrated with your service!",
        "external_id": "fb-angry",
    }
    create_resp = await async_client.post("/api/v1/inquiries/", json=payload)
    assert create_resp.status_code == 201
    inquiry_id = create_resp.json()["id"]

    escalate_resp = await async_client.post(f"/api/v1/inquiries/{inquiry_id}/escalate")
    assert escalate_resp.status_code == 200
    data = escalate_resp.json()
    assert data["status"] == "escalated"
    assert data["checkpoint_id"].startswith("CP-02")
    assert data["stage"] == "Manager Review"


async def test_list_inquiries_with_status_filter(async_client, db_session):
    payload1 = {"source": "walkin", "content": "Nice place"}
    payload2 = {"source": "phone", "content": "Bad experience", "external_id": "p2"}

    resp1 = await async_client.post("/api/v1/inquiries/", json=payload1)
    resp2 = await async_client.post("/api/v1/inquiries/", json=payload2)
    assert resp1.status_code == 201
    assert resp2.status_code == 201

    id1 = resp1.json()["id"]
    await async_client.post(f"/api/v1/inquiries/{id1}/respond")

    list_resp = await async_client.get("/api/v1/inquiries/?status=new")
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert all(item["status"] == "new" for item in items)

    list_resp2 = await async_client.get("/api/v1/inquiries/?status=responded")
    assert list_resp2.status_code == 200
    items2 = list_resp2.json()
    assert any(item["id"] == id1 for item in items2)


async def test_list_inquiries_with_source_filter(async_client, db_session):
    payload = {"source": "tiktok", "content": "Cool videos"}
    await async_client.post("/api/v1/inquiries/", json=payload)

    list_resp = await async_client.get("/api/v1/inquiries/?source=tiktok")
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert len(items) >= 1
    assert all(item["source"] == "tiktok" for item in items)
