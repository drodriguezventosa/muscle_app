"""Integration tests for the coaching endpoints against a real database."""

from datetime import date, timedelta

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.infrastructure.persistence.models.exercise import ExerciseModel
from app.infrastructure.persistence.models.user import UserModel
from app.infrastructure.persistence.seed import DEMO_STUDENTS, seed
from tests.integration.conftest import SEED_WEEKS

TRAINER_EMAIL = "entrenador@demo.muscleapp"
CLIENT_EMAIL = "alumno@demo.muscleapp"


async def _auth(api_client: AsyncClient, email: str) -> dict[str, str]:
    response = await api_client.post(
        "/api/v1/auth/login", json={"email": email, "password": get_settings().demo_password}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def _exercise_id(session: AsyncSession) -> int:
    """Any catalog exercise: the sync only cares that the id exists."""
    return int((await session.scalars(select(ExerciseModel.id).limit(1))).one())


async def test_the_coaching_endpoints_require_a_token(api_client: AsyncClient) -> None:
    assert (await api_client.get("/api/v1/coaching/students")).status_code == 401
    assert (await api_client.get("/api/v1/coaching/students/1")).status_code == 401
    assert (await api_client.get("/api/v1/coaching/me/progress")).status_code == 401
    assert (await api_client.post("/api/v1/coaching/me/progress", json={})).status_code == 401


async def test_a_client_cannot_read_the_roster(api_client: AsyncClient) -> None:
    headers = await _auth(api_client, CLIENT_EMAIL)
    response = await api_client.get("/api/v1/coaching/students", headers=headers)
    assert response.status_code == 403


async def test_the_trainer_sees_the_seeded_roster(api_client: AsyncClient) -> None:
    headers = await _auth(api_client, TRAINER_EMAIL)
    response = await api_client.get("/api/v1/coaching/students", headers=headers)

    assert response.status_code == 200
    students = response.json()
    assert len(students) == len(DEMO_STUDENTS)
    first = students[0]
    assert first["bmi"] and first["age"] and first["goal"]
    assert first["sessions_last_30d"] > 0


async def test_the_trainer_gets_a_students_evolution(api_client: AsyncClient) -> None:
    headers = await _auth(api_client, TRAINER_EMAIL)
    students = (await api_client.get("/api/v1/coaching/students", headers=headers)).json()

    response = await api_client.get(
        f"/api/v1/coaching/students/{students[0]['id']}", headers=headers
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["adherence"]) == 12
    assert body["body_weight"], "the seeded history includes weekly weigh-ins"
    assert body["strength"], "the seeded history includes barbell work"
    assert body["total_sessions"] > 0
    points = body["strength"][0]["points"]
    assert points[-1]["value"] >= points[0]["value"], "the seeded students progress"


async def test_a_student_that_is_not_on_the_roster_is_404(
    api_client: AsyncClient, session: AsyncSession
) -> None:
    await seed(session, weeks=SEED_WEEKS)
    headers = await _auth(api_client, TRAINER_EMAIL)
    # The trainer's own id is a real user, but not one of their students.
    trainer_id = await session.scalar(select(UserModel.id).where(UserModel.email == TRAINER_EMAIL))

    assert (
        await api_client.get(f"/api/v1/coaching/students/{trainer_id}", headers=headers)
    ).status_code == 404
    assert (
        await api_client.get("/api/v1/coaching/students/999999", headers=headers)
    ).status_code == 404


async def test_a_student_syncs_progress_and_reads_it_back(
    api_client: AsyncClient, session: AsyncSession
) -> None:
    headers = await _auth(api_client, CLIENT_EMAIL)
    exercise_id = await _exercise_id(session)
    today = date.today()
    payload = {
        "sessions": [
            {
                "exercise_id": exercise_id,
                "logged_on": today.isoformat(),
                "weight_kg": 82.5,
                "reps": 6,
                "completed": True,
            }
        ],
        "weight_kg": 79.2,
        "height_cm": 180,
        "age": 30,
    }

    response = await api_client.post("/api/v1/coaching/me/progress", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["synced"] == 1

    # Re-sending the same day must update, not duplicate.
    again = await api_client.post("/api/v1/coaching/me/progress", json=payload, headers=headers)
    assert again.json()["synced"] == 1

    mine = (await api_client.get("/api/v1/coaching/me/progress", headers=headers)).json()
    assert mine["student"]["height_cm"] == 180
    assert mine["student"]["weight_kg"] == 79.2
    today_points = [
        point
        for progression in mine["strength"]
        for point in progression["points"]
        if point["on"] == today.isoformat()
    ]
    assert today_points, "the synced session shows up in the student's own evolution"


async def test_the_trainer_sees_what_their_student_synced(
    api_client: AsyncClient, session: AsyncSession
) -> None:
    client_headers = await _auth(api_client, CLIENT_EMAIL)
    exercise_id = await _exercise_id(session)
    await api_client.post(
        "/api/v1/coaching/me/progress",
        json={
            "weight_kg": 88.8,
            "sessions": [
                {
                    "exercise_id": exercise_id,
                    "logged_on": date.today().isoformat(),
                    "weight_kg": 100.0,
                    "reps": 3,
                    "completed": True,
                }
            ],
        },
        headers=client_headers,
    )

    trainer_headers = await _auth(api_client, TRAINER_EMAIL)
    roster = (await api_client.get("/api/v1/coaching/students", headers=trainer_headers)).json()
    javier = next(student for student in roster if student["name"] == DEMO_STUDENTS[0].name)

    assert javier["weight_kg"] == 88.8
    detail = (
        await api_client.get(f"/api/v1/coaching/students/{javier['id']}", headers=trainer_headers)
    ).json()
    assert detail["body_weight"][-1]["value"] == 88.8


async def test_implausible_sessions_are_rejected(api_client: AsyncClient) -> None:
    headers = await _auth(api_client, CLIENT_EMAIL)
    # Two days ahead: one day of slack is allowed for clients in timezones
    # that are already on tomorrow.
    tomorrow = (date.today() + timedelta(days=2)).isoformat()
    session_payload = {
        "exercise_id": 1,
        "logged_on": tomorrow,
        "weight_kg": 50,
        "reps": 5,
        "completed": True,
    }

    response = await api_client.post(
        "/api/v1/coaching/me/progress", json={"sessions": [session_payload]}, headers=headers
    )
    assert response.status_code == 422

    too_heavy = {**session_payload, "logged_on": date.today().isoformat(), "weight_kg": 5000}
    assert (
        await api_client.post(
            "/api/v1/coaching/me/progress", json={"sessions": [too_heavy]}, headers=headers
        )
    ).status_code == 422


async def test_sessions_for_unknown_exercises_are_ignored(api_client: AsyncClient) -> None:
    headers = await _auth(api_client, CLIENT_EMAIL)
    response = await api_client.post(
        "/api/v1/coaching/me/progress",
        json={
            "sessions": [
                {
                    "exercise_id": 999999,
                    "logged_on": date.today().isoformat(),
                    "weight_kg": 50,
                    "reps": 5,
                    "completed": True,
                }
            ]
        },
        headers=headers,
    )
    # A stale browser entry must not fail the whole sync.
    assert response.status_code == 200
    assert response.json()["synced"] == 0


async def test_the_trainers_on_offer_are_public(api_client: AsyncClient) -> None:
    # Browsing needs no account: the sign-in comes when hiring.
    response = await api_client.get("/api/v1/coaching/trainers")

    assert response.status_code == 200
    trainers = response.json()
    assert len(trainers) >= 4
    assert {"id", "name", "specialty", "rating", "price_per_month", "students"} <= set(trainers[0])


async def test_the_seeded_student_already_has_a_trainer(api_client: AsyncClient) -> None:
    headers = await _auth(api_client, CLIENT_EMAIL)
    response = await api_client.get("/api/v1/coaching/me/trainer", headers=headers)

    assert response.status_code == 200
    assert response.json()["name"] == "Ana López"


async def test_hiring_another_trainer_replaces_the_current_one(api_client: AsyncClient) -> None:
    headers = await _auth(api_client, CLIENT_EMAIL)
    trainers = (await api_client.get("/api/v1/coaching/trainers")).json()
    other = next(trainer for trainer in trainers if trainer["name"] != "Ana López")

    hired = await api_client.put(
        "/api/v1/coaching/me/trainer", json={"trainer_id": other["id"]}, headers=headers
    )

    assert hired.status_code == 200
    assert hired.json()["id"] == other["id"]
    # One trainer per student: the previous link is gone, not stacked.
    assert (await api_client.get("/api/v1/coaching/me/trainer", headers=headers)).json()["id"] == (
        other["id"]
    )


async def test_the_new_trainer_sees_the_student_and_the_old_one_does_not(
    api_client: AsyncClient,
) -> None:
    student = await _auth(api_client, CLIENT_EMAIL)
    student_id = (await api_client.get("/api/v1/auth/me", headers=student)).json()["id"]
    trainers = (await api_client.get("/api/v1/coaching/trainers")).json()
    other = next(trainer for trainer in trainers if trainer["name"] != "Ana López")
    await api_client.put(
        "/api/v1/coaching/me/trainer", json={"trainer_id": other["id"]}, headers=student
    )

    # Ana can no longer read a student who moved on.
    ana = await _auth(api_client, TRAINER_EMAIL)
    assert (
        await api_client.get(f"/api/v1/coaching/students/{student_id}", headers=ana)
    ).status_code == 404
    roster = (await api_client.get("/api/v1/coaching/students", headers=ana)).json()
    assert student_id not in [entry["id"] for entry in roster]


async def test_hiring_a_user_who_is_not_a_trainer_is_404(api_client: AsyncClient) -> None:
    headers = await _auth(api_client, CLIENT_EMAIL)
    me = (await api_client.get("/api/v1/auth/me", headers=headers)).json()

    response = await api_client.put(
        "/api/v1/coaching/me/trainer", json={"trainer_id": me["id"]}, headers=headers
    )
    assert response.status_code == 404


async def test_cancelling_leaves_the_student_without_a_trainer(api_client: AsyncClient) -> None:
    headers = await _auth(api_client, CLIENT_EMAIL)

    assert (
        await api_client.delete("/api/v1/coaching/me/trainer", headers=headers)
    ).status_code == 204

    assert (await api_client.get("/api/v1/coaching/me/trainer", headers=headers)).json() is None
