import random
from datetime import UTC, datetime, timedelta
from uuid import UUID

from exercise_library.application import ExerciseApplication, ReviewExerciseStats
from exercise_library.models import ReviewStatus
from exercise_library.review import compute_weight, select_next_exercise


def _stats(
    total: int,
    failures: int,
    last: datetime | None,
    exercise_uuid: UUID | None = None,
    recent_failures: int | None = None,
) -> ReviewExerciseStats:
    return ReviewExerciseStats(
        exercise_uuid=exercise_uuid or UUID(int=0),
        total_reviews=total,
        failures=failures,
        last_reviewed_at=last,
        recent_failures=failures if recent_failures is None else recent_failures,
    )


def test_never_reviewed_gets_high_weight() -> None:
    now = datetime.now(tz=UTC)

    never = compute_weight(_stats(0, 0, None), now=now)
    recent = compute_weight(_stats(5, 0, now - timedelta(hours=1)), now=now)

    assert never > recent


def test_older_reviews_weigh_more_than_recent() -> None:
    now = datetime.now(tz=UTC)

    old = compute_weight(_stats(3, 0, now - timedelta(days=60)), now=now)
    new = compute_weight(_stats(3, 0, now - timedelta(days=1)), now=now)

    assert old > new


def test_failures_increase_weight() -> None:
    now = datetime.now(tz=UTC)

    struggling = compute_weight(_stats(4, 3, now - timedelta(days=7)), now=now)
    solid = compute_weight(_stats(4, 0, now - timedelta(days=7)), now=now)

    assert struggling > solid


def test_archived_failures_do_not_boost() -> None:
    now = datetime.now(tz=UTC)

    stale = compute_weight(
        _stats(30, 25, now - timedelta(days=7), recent_failures=0), now=now
    )
    clean = compute_weight(_stats(30, 0, now - timedelta(days=7)), now=now)

    assert stale == clean


def test_more_reviews_damp_weight() -> None:
    now = datetime.now(tz=UTC)
    moment = now - timedelta(days=7)

    frequent = compute_weight(_stats(20, 0, moment), now=now)
    rare = compute_weight(_stats(1, 0, moment), now=now)

    assert rare > frequent


def test_weight_is_positive() -> None:
    now = datetime.now(tz=UTC)
    assert compute_weight(_stats(0, 0, None), now=now) > 0
    assert compute_weight(_stats(10, 5, now), now=now) > 0


def test_select_next_exercise_with_seeded_rng(
    application: ExerciseApplication,
) -> None:
    application.add_exercise(prompt="p", answer="a", identifier="a::one")
    application.add_exercise(prompt="p", answer="a", identifier="a::two")

    rng = random.Random(42)
    first = select_next_exercise(application, rng=random.Random(42))
    second = select_next_exercise(application, rng=rng)

    assert first is not None
    assert second is not None


def test_select_next_exercise_returns_none_when_empty(
    application: ExerciseApplication,
) -> None:
    assert select_next_exercise(application) is None


def test_select_next_exercise_filters_by_status(
    application: ExerciseApplication,
) -> None:
    application.add_exercise(prompt="p", answer="a", identifier="b::new")
    application.add_exercise(prompt="p", answer="a", identifier="b::seen")
    application.record_review("b::seen", "good")

    new_only = select_next_exercise(
        application, status=ReviewStatus.NEW, rng=random.Random(1)
    )
    reviewed_only = select_next_exercise(
        application, status=ReviewStatus.REVIEWED, rng=random.Random(1)
    )

    assert new_only is not None and new_only.identifier == "b::new"
    assert reviewed_only is not None and reviewed_only.identifier == "b::seen"
