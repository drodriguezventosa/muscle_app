"""Integration tests for the training calendar against a real database."""

from datetime import date, timedelta

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.infrastructure.persistence.models.exercise import ExerciseModel
from app.infrastructure.persistence.models.plan import PlanItemModel

TRAINER_EMAIL = "entrenador@demo.muscleapp"
CLIENT_EMAIL = "alumno@demo.muscleapp"


async def _auth(api_client: AsyncClient, email: str) -> dict[str, str]:
    response = await api_client.post(
        "/api/v1/auth/login", json={"email": email, "password": get_settings().demo_password}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def _student_id(api_client: AsyncClient, headers: dict[str, str]) -> int:
    roster = (await api_client.get("/api/v1/coaching/students", headers=headers)).json()
    return int(next(s for s in roster if s["name"] == "Javier M.")["id"])


async def _exercise_id(session: AsyncSession) -> int:
    return int((await session.scalars(select(ExerciseModel.id).limit(1))).one())


async def test_the_calendar_endpoints_require_the_right_role(api_client: AsyncClient) -> None:
    assert (await api_client.get("/api/v1/coaching/me/plan")).status_code == 401

    client = await _auth(api_client, CLIENT_EMAIL)
    # A student may read their own calendar but not write anyone's.
    assert (await api_client.get("/api/v1/coaching/me/plan", headers=client)).status_code == 200
    scheduling = await api_client.post(
        "/api/v1/coaching/students/1/plan",
        json={"exercise_id": 1, "scheduled_on": date.today().isoformat()},
        headers=client,
    )
    assert scheduling.status_code == 403


async def test_the_seed_puts_this_week_on_the_calendar(api_client: AsyncClient) -> None:
    headers = await _auth(api_client, CLIENT_EMAIL)
    plan = (await api_client.get("/api/v1/coaching/me/plan", headers=headers)).json()

    assert plan, "the demo student opens the app with a routine already scheduled"
    assert {entry["status"] for entry in plan} <= {"pending", "done", "partial", "missed"}


async def test_a_trainer_schedules_and_the_student_sees_it(
    api_client: AsyncClient, session: AsyncSession
) -> None:
    trainer = await _auth(api_client, TRAINER_EMAIL)
    student_id = await _student_id(api_client, trainer)
    exercise_id = await _exercise_id(session)
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    created = await api_client.post(
        f"/api/v1/coaching/students/{student_id}/plan",
        json={
            "exercise_id": exercise_id,
            "scheduled_on": tomorrow,
            "target_sets": 4,
            "target_reps": 6,
            "target_weight_kg": 90,
            "notes": "Sube 2,5 kg si sale limpio",
        },
        headers=trainer,
    )
    assert created.status_code == 201, created.text
    assert created.json()["status"] == "pending"

    student = await _auth(api_client, CLIENT_EMAIL)
    plan = (
        await api_client.get(
            f"/api/v1/coaching/me/plan?from={tomorrow}&to={tomorrow}", headers=student
        )
    ).json()
    mine = next(entry for entry in plan if entry["id"] == created.json()["id"])
    assert mine["target_weight_kg"] == 90
    assert mine["notes"] == "Sube 2,5 kg si sale limpio"


async def test_changing_trainer_hands_the_calendar_over(
    api_client: AsyncClient, session: AsyncSession
) -> None:
    """The plan belongs to the trainer-student pair, so hiring another one resets it.

    Each trainer keeps their own calendar for the same student: the new one starts
    from an empty week and writes their own, and the previous one's prescriptions
    stay with them rather than being inherited or deleted.
    """
    student = await _auth(api_client, CLIENT_EMAIL)
    monday = date.today() - timedelta(days=date.today().weekday())
    sunday = monday + timedelta(days=6)
    window = f"from={monday.isoformat()}&to={sunday.isoformat()}"
    seeded = (await api_client.get(f"/api/v1/coaching/me/plan?{window}", headers=student)).json()
    assert seeded, "the seed leaves this week on Ana's calendar"

    trainers = (await api_client.get("/api/v1/coaching/trainers")).json()
    marco = next(trainer for trainer in trainers if trainer["name"] != "Ana López")
    hired = await api_client.put(
        "/api/v1/coaching/me/trainer", json={"trainer_id": marco["id"]}, headers=student
    )
    assert hired.status_code == 200

    # Marco has not scheduled anything yet, so the week is his to fill.
    after = (await api_client.get(f"/api/v1/coaching/me/plan?{window}", headers=student)).json()
    assert after == []

    # What Ana had prescribed is no longer the student's to report on.
    report = await api_client.post(
        f"/api/v1/coaching/me/plan/{seeded[0]['id']}/report",
        json={"weight_kg": 80, "reps": 8, "sets": 3},
        headers=student,
    )
    assert report.status_code == 404

    # What Marco prescribes is what the student now sees. He is written straight
    # into the database because only the advertised trainer can sign in
    # (ADR-0024), and the point here is the read path, keyed by the pair.
    exercise_id = await _exercise_id(session)
    tomorrow = date.today() + timedelta(days=1)
    student_id = (await api_client.get("/api/v1/auth/me", headers=student)).json()["id"]
    session.add(
        PlanItemModel(
            trainer_id=marco["id"],
            student_id=student_id,
            exercise_id=exercise_id,
            scheduled_on=tomorrow,
            target_sets=3,
            target_reps=10,
            target_weight_kg=60.0,
        )
    )
    await session.commit()

    plan = (
        await api_client.get(
            f"/api/v1/coaching/me/plan?from={tomorrow.isoformat()}&to={tomorrow.isoformat()}",
            headers=student,
        )
    ).json()
    assert [entry["target_reps"] for entry in plan] == [10]


async def test_rescheduling_the_same_day_edits_the_target(
    api_client: AsyncClient, session: AsyncSession
) -> None:
    trainer = await _auth(api_client, TRAINER_EMAIL)
    student_id = await _student_id(api_client, trainer)
    exercise_id = await _exercise_id(session)
    day = (date.today() + timedelta(days=2)).isoformat()
    body = {"exercise_id": exercise_id, "scheduled_on": day, "target_weight_kg": 80}

    first = await api_client.post(
        f"/api/v1/coaching/students/{student_id}/plan", json=body, headers=trainer
    )
    second = await api_client.post(
        f"/api/v1/coaching/students/{student_id}/plan",
        json={**body, "target_weight_kg": 85},
        headers=trainer,
    )

    assert first.json()["id"] == second.json()["id"], "the same slot, not a duplicate"
    assert second.json()["target_weight_kg"] == 85


async def test_the_student_reports_what_they_lifted(
    api_client: AsyncClient, session: AsyncSession
) -> None:
    trainer = await _auth(api_client, TRAINER_EMAIL)
    student_id = await _student_id(api_client, trainer)
    exercise_id = await _exercise_id(session)
    today = date.today().isoformat()
    created = await api_client.post(
        f"/api/v1/coaching/students/{student_id}/plan",
        json={
            "exercise_id": exercise_id,
            "scheduled_on": today,
            "target_reps": 8,
            "target_weight_kg": 100,
        },
        headers=trainer,
    )
    item_id = created.json()["id"]

    student = await _auth(api_client, CLIENT_EMAIL)
    # Short of the target: the plan says so instead of calling it done.
    partial = await api_client.post(
        f"/api/v1/coaching/me/plan/{item_id}/report",
        json={"weight_kg": 92.5, "reps": 8, "sets": 3},
        headers=student,
    )
    assert partial.status_code == 200
    assert partial.json()["status"] == "partial"
    assert partial.json()["done_weight_kg"] == 92.5
    assert partial.json()["done_sets"] == 3

    # One set short of the plan is partial too, even at the full load.
    short_sets = await api_client.post(
        f"/api/v1/coaching/me/plan/{item_id}/report",
        json={"weight_kg": 100, "reps": 8, "sets": 2},
        headers=student,
    )
    assert short_sets.json()["status"] == "partial"

    # Reporting again with the full load closes it.
    done = await api_client.post(
        f"/api/v1/coaching/me/plan/{item_id}/report",
        json={"weight_kg": 100, "reps": 8, "sets": 3},
        headers=student,
    )
    assert done.json()["status"] == "done"

    # And it reached the trainer's dashboard as an ordinary session.
    detail = (
        await api_client.get(f"/api/v1/coaching/students/{student_id}", headers=trainer)
    ).json()
    today_points = [
        point
        for progression in detail["strength"]
        for point in progression["points"]
        if point["on"] == today
    ]
    assert today_points, "a reported session feeds the evolution charts"


async def test_a_trainer_cannot_touch_a_student_that_is_not_theirs(
    api_client: AsyncClient, session: AsyncSession
) -> None:
    trainer = await _auth(api_client, TRAINER_EMAIL)
    exercise_id = await _exercise_id(session)

    response = await api_client.post(
        "/api/v1/coaching/students/999999/plan",
        json={"exercise_id": exercise_id, "scheduled_on": date.today().isoformat()},
        headers=trainer,
    )
    assert response.status_code == 404

    assert (
        await api_client.get("/api/v1/coaching/students/999999/plan", headers=trainer)
    ).status_code == 404


async def test_removing_a_scheduled_exercise(
    api_client: AsyncClient, session: AsyncSession
) -> None:
    trainer = await _auth(api_client, TRAINER_EMAIL)
    student_id = await _student_id(api_client, trainer)
    exercise_id = await _exercise_id(session)
    day = (date.today() + timedelta(days=3)).isoformat()
    created = await api_client.post(
        f"/api/v1/coaching/students/{student_id}/plan",
        json={"exercise_id": exercise_id, "scheduled_on": day},
        headers=trainer,
    )
    item_id = created.json()["id"]

    assert (
        await api_client.delete(f"/api/v1/coaching/plan/{item_id}", headers=trainer)
    ).status_code == 204
    # Gone, and saying so twice is a 404 rather than a silent success.
    assert (
        await api_client.delete(f"/api/v1/coaching/plan/{item_id}", headers=trainer)
    ).status_code == 404


async def test_scheduling_an_unknown_exercise_is_422(api_client: AsyncClient) -> None:
    trainer = await _auth(api_client, TRAINER_EMAIL)
    student_id = await _student_id(api_client, trainer)

    response = await api_client.post(
        f"/api/v1/coaching/students/{student_id}/plan",
        json={"exercise_id": 999999, "scheduled_on": date.today().isoformat()},
        headers=trainer,
    )
    assert response.status_code == 422


async def test_the_catalog_search_finds_exercises_in_either_language(
    api_client: AsyncClient,
) -> None:
    spanish = (await api_client.get("/api/v1/exercises?q=sentadilla&limit=5")).json()
    english = (await api_client.get("/api/v1/exercises?q=squat&limit=5&lang=en")).json()

    assert spanish and english
    assert all("entadilla" in exercise["name"] for exercise in spanish)
    assert len((await api_client.get("/api/v1/exercises?limit=3")).json()) == 3
