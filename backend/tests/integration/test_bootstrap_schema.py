"""Integration tests for the boot-time schema reconciliation.

The deployed app runs `python -m app.bootstrap` and not Alembic, so these two
functions *are* the deploy path for a schema change. Both were written after a
change reached production silently unapplied — a missing column (500s on every
query that selected it) and a changed unique constraint (no error at all, just a
rule that stopped being enforced) — which is why each is tested against a real
database shaped like the deployed one.
"""

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.bootstrap import _add_missing_columns, _reconcile_unique_constraints

LEGACY_PAIR_CONSTRAINT = (
    "ALTER TABLE trainer_students ADD CONSTRAINT uq_trainer_student UNIQUE (trainer_id, student_id)"
)
DROP_CONSTRAINT = "ALTER TABLE trainer_students DROP CONSTRAINT uq_trainer_student"


async def _unique_columns(engine: AsyncEngine, table: str, name: str) -> list[str] | None:
    async with engine.begin() as conn:
        constraints = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_unique_constraints(table)
        )
    for constraint in constraints:
        if constraint["name"] == name:
            return list(constraint["column_names"])
    return None


async def _make_user(engine: AsyncEngine, email: str, role: str) -> int:
    async with engine.begin() as conn:
        user_id = await conn.scalar(
            text(
                "INSERT INTO users (email, name, password_hash, role) "
                "VALUES (:email, :email, 'x', :role) RETURNING id"
            ),
            {"email": email, "role": role},
        )
    return int(user_id or 0)


async def test_a_changed_unique_constraint_is_replaced_on_boot(db_engine: AsyncEngine) -> None:
    # The shape the deployed table was left with: unique on the pair, so a
    # student could hold two trainers.
    async with db_engine.begin() as conn:
        await conn.execute(text(DROP_CONSTRAINT))
        await conn.execute(text(LEGACY_PAIR_CONSTRAINT))
    assert await _unique_columns(db_engine, "trainer_students", "uq_trainer_student") == [
        "trainer_id",
        "student_id",
    ]

    async with db_engine.begin() as conn:
        await conn.run_sync(_reconcile_unique_constraints)

    assert await _unique_columns(db_engine, "trainer_students", "uq_trainer_student") == [
        "student_id"
    ]


async def test_a_constraint_the_existing_rows_would_violate_is_kept(
    db_engine: AsyncEngine,
) -> None:
    # Two trainers for one student: exactly what the old constraint allowed and
    # the new one forbids. Tightening it here would fail, so the old one stays
    # and the boot reports it instead of crashing the deploy.
    async with db_engine.begin() as conn:
        await conn.execute(text(DROP_CONSTRAINT))
        await conn.execute(text(LEGACY_PAIR_CONSTRAINT))
    student = await _make_user(db_engine, "two@demo.test", "client")
    first = await _make_user(db_engine, "one-trainer@demo.test", "trainer")
    second = await _make_user(db_engine, "other-trainer@demo.test", "trainer")
    async with db_engine.begin() as conn:
        await conn.execute(
            text("INSERT INTO trainer_students (trainer_id, student_id) VALUES (:a, :s), (:b, :s)"),
            {"a": first, "b": second, "s": student},
        )

    async with db_engine.begin() as conn:
        await conn.run_sync(_reconcile_unique_constraints)

    assert await _unique_columns(db_engine, "trainer_students", "uq_trainer_student") == [
        "trainer_id",
        "student_id",
    ]
    # The boot went on: the rest of the schema is still reconciled.
    async with db_engine.begin() as conn:
        rows = await conn.scalar(text("SELECT count(*) FROM trainer_students"))
    assert rows == 2


async def test_a_missing_constraint_is_created_on_boot(db_engine: AsyncEngine) -> None:
    async with db_engine.begin() as conn:
        await conn.execute(text(DROP_CONSTRAINT))
    assert await _unique_columns(db_engine, "trainer_students", "uq_trainer_student") is None

    async with db_engine.begin() as conn:
        await conn.run_sync(_reconcile_unique_constraints)

    assert await _unique_columns(db_engine, "trainer_students", "uq_trainer_student") == [
        "student_id"
    ]


async def test_a_column_the_deployed_table_lacks_is_added_on_boot(db_engine: AsyncEngine) -> None:
    # How `workout_logs.sets` reached production missing: `create_all` had made
    # the table on an earlier release and never revisited it.
    async with db_engine.begin() as conn:
        await conn.execute(text("ALTER TABLE workout_logs DROP COLUMN sets"))

    async with db_engine.begin() as conn:
        await conn.run_sync(_add_missing_columns)

    async with db_engine.begin() as conn:
        columns = await conn.run_sync(
            lambda sync_conn: {c["name"] for c in inspect(sync_conn).get_columns("workout_logs")}
        )
    assert "sets" in columns
