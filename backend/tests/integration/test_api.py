"""Integration tests for the public explorer endpoints (against a seeded DB)."""

from httpx import AsyncClient


async def test_list_muscles(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/v1/muscles")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 10
    assert {"chest", "biceps"} <= {m["svg_id"] for m in body}


async def test_get_muscle_found_default_spanish(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/v1/muscles/chest")
    assert response.status_code == 200
    assert response.json()["name"] == "Pectoral mayor"
    assert response.json()["muscle_group"] == "chest"


async def test_get_muscle_translated_to_english(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/v1/muscles/chest?lang=en")
    assert response.status_code == 200
    assert response.json()["name"] == "Pectoralis major"


async def test_get_muscle_not_found(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/v1/muscles/does-not-exist")
    assert response.status_code == 404


async def test_list_muscle_exercises(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/v1/muscles/chest/exercises")
    assert response.status_code == 200
    names = {e["name"] for e in response.json()}
    assert "Flexiones" in names  # default Spanish
    assert "Press de banca con barra" in names

    english = await api_client.get("/api/v1/muscles/chest/exercises?lang=en")
    assert "Push-up" in {e["name"] for e in english.json()}

    # The demonstration video is localized too (ES vs EN URLs differ).
    push_up_es = next(e for e in response.json() if e["name"] == "Flexiones")
    push_up_en = next(e for e in english.json() if e["name"] == "Push-up")
    assert push_up_es["video_url"] and push_up_en["video_url"]
    assert push_up_es["video_url"] != push_up_en["video_url"]


async def test_list_muscle_exercises_unknown_muscle_is_404(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/v1/muscles/nope/exercises")
    assert response.status_code == 404


async def test_get_exercise(api_client: AsyncClient) -> None:
    # Discover a real id via the chest exercises listing, then fetch it.
    listing = await api_client.get("/api/v1/muscles/chest/exercises")
    exercise_id = listing.json()[0]["id"]

    response = await api_client.get(f"/api/v1/exercises/{exercise_id}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == exercise_id
    assert "targeted_muscles" in payload
    assert payload["equipment"] in {"bodyweight", "barbell", "dumbbell", "cable", "machine"}


async def test_get_exercise_not_found(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/v1/exercises/999999")
    assert response.status_code == 404
