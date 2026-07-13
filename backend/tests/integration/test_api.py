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


async def test_filter_exercises_by_equipment_and_difficulty(api_client: AsyncClient) -> None:
    all_chest = (await api_client.get("/api/v1/muscles/chest/exercises")).json()

    only_bodyweight = await api_client.get(
        "/api/v1/muscles/chest/exercises", params={"equipment": "bodyweight"}
    )
    assert only_bodyweight.status_code == 200
    bodyweight = only_bodyweight.json()
    assert 0 < len(bodyweight) < len(all_chest)
    assert all(e["equipment"] == "bodyweight" for e in bodyweight)

    beginners = await api_client.get(
        "/api/v1/muscles/chest/exercises", params={"difficulty": "beginner"}
    )
    assert all(e["difficulty"] == "beginner" for e in beginners.json())


async def test_exercises_have_video_or_steps(api_client: AsyncClient) -> None:
    chest = (await api_client.get("/api/v1/muscles/chest/exercises")).json()
    by_name = {e["name"]: e for e in chest}

    # Push-up ships with a demonstration video and also readable how-to steps.
    assert by_name["Flexiones"]["video_url"]
    assert len(by_name["Flexiones"]["steps"]) >= 2

    # Every exercise has at least one example: a video or how-to steps.
    assert all(e["video_url"] or e["steps"] for e in chest)

    # Steps are still provided (readable in a collapsible) and localized.
    traps = (await api_client.get("/api/v1/muscles/traps/exercises")).json()
    shrug = next(e for e in traps if e["name"] == "Encogimientos con barra")
    assert len(shrug["steps"]) >= 2

    english = (await api_client.get("/api/v1/muscles/traps/exercises?lang=en")).json()
    shrug_en = next(e for e in english if e["name"] == "Barbell shrug")
    assert shrug_en["steps"] and shrug_en["steps"] != shrug["steps"]


async def test_active_muscles_reflect_filters(api_client: AsyncClient) -> None:
    # With no filter every muscle that has exercises is active.
    unfiltered = await api_client.get("/api/v1/muscles/active")
    assert unfiltered.status_code == 200
    assert len(unfiltered.json()) == 10

    # Machine exercises only exist for a subset of muscles (not the chest).
    machine = await api_client.get("/api/v1/muscles/active", params={"equipment": "machine"})
    svg_ids = {m["svg_id"] for m in machine.json()}
    assert "quads" in svg_ids
    assert "chest" not in svg_ids
    assert len(svg_ids) < 10


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


async def test_generate_workout(api_client: AsyncClient) -> None:
    body = {"goal": "hypertrophy", "experience": "intermediate", "height_cm": 180, "weight_kg": 80}
    response = await api_client.post("/api/v1/workouts/generate", json=body)
    assert response.status_code == 200
    data = response.json()
    assert data["goal"] == "hypertrophy"
    assert data["bmi"] == 24.7  # 80 / 1.8^2
    assert data["bmi_category"] == "normal"
    assert len(data["items"]) >= 3
    first = data["items"][0]
    assert first["sets"] == 4 and first["reps"] == "8-12" and first["rest_seconds"] == 75
    assert first["exercise"]["name"]


async def test_generate_workout_validates_attributes(api_client: AsyncClient) -> None:
    bad = {"goal": "strength", "experience": "beginner", "height_cm": 10, "weight_kg": 80}
    response = await api_client.post("/api/v1/workouts/generate", json=bad)
    assert response.status_code == 422
