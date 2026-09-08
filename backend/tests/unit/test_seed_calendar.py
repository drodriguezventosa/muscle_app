"""Keep the day the integration suite runs on valid for the demo data.

The seeded history is generated around "today" and follows training blocks with
a deload every ninth week, so the frozen date must sit where the seeded window
holds trained weeks and none of them is a deload. If the seed's rhythm or the
frozen date changes, these fail with a reason instead of a progress assertion
failing somewhere in the coaching API tests.
"""

from app.infrastructure.persistence import seed
from tests.integration.conftest import FROZEN_NOW, SEED_WEEKS

FROZEN_DAY = FROZEN_NOW.date()


def test_the_frozen_day_falls_inside_the_demo_year() -> None:
    assert FROZEN_DAY.year == seed.DEMO_YEAR


def test_the_seeded_window_has_no_deload_week() -> None:
    weeks = seed._demo_weeks(FROZEN_DAY, SEED_WEEKS)

    assert len(weeks) == SEED_WEEKS + 1, "past weeks, the current one and the next"
    assert all(number % seed._DELOAD_EVERY for number, _ in weeks)


def test_the_seeded_loads_never_drop_within_the_window() -> None:
    trained = [
        number
        for number, monday in seed._demo_weeks(FROZEN_DAY, SEED_WEEKS)
        if monday <= FROZEN_DAY
    ]
    loads = [seed._load_at(80.0, week) for week in trained]

    assert trained, "some of the seeded weeks are already trained"
    assert loads == sorted(loads)
