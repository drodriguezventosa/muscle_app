"""Integration tests for the recommendation chatbot endpoint."""

from httpx import AsyncClient


async def test_recommend_returns_reply_and_grounded_exercises(api_client: AsyncClient) -> None:
    response = await api_client.post(
        "/api/v1/chat/recommendations",
        json={"message": "quiero entrenar el pecho en casa sin material"},
    )
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["reply"], str) and body["reply"].strip()
    assert len(body["exercises"]) > 0
    assert "targeted_muscles" in body["exercises"][0]


async def test_recommend_respects_equipment_filter(api_client: AsyncClient) -> None:
    response = await api_client.post(
        "/api/v1/chat/recommendations",
        json={"message": "algo de fuerza", "equipment": "barbell"},
    )
    assert response.status_code == 200
    equipments = {e["equipment"] for e in response.json()["exercises"]}
    assert equipments <= {"barbell"}


async def test_recommend_rejects_empty_message(api_client: AsyncClient) -> None:
    response = await api_client.post("/api/v1/chat/recommendations", json={"message": ""})
    assert response.status_code == 422


async def test_recommend_rejects_too_long_message(api_client: AsyncClient) -> None:
    response = await api_client.post("/api/v1/chat/recommendations", json={"message": "x" * 501})
    assert response.status_code == 422
