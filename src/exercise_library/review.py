import math
import random
from datetime import UTC, datetime

from exercise_library.application import ExerciseApplication, ReviewExerciseStats
from exercise_library.models import Exercise, ReviewStatus

# How long a never-reviewed exercise has "waited", in days, for weight purposes.
NEVER_REVIEWED_DAYS_SINCE_LAST_REVIEW = 30.0

_SECONDS_PER_DAY = 86_400.0


def compute_weight(
    stats: ReviewExerciseStats,
    now: datetime | None = None,
) -> float:
    """Return the selection weight for an exercise's review stats.

    Higher weight means the exercise is more likely to be picked next.
    The signal combines:

    - recency: exercises not reviewed recently weigh more; never-reviewed
      exercises get the maximum recency term;
    - count damping: exercises reviewed many times weigh less;
    - failure boost: recent failed reviews weigh more. Only failures
      inside the retained window are considered; archived (lifetime)
      failures do not boost the weight.

    Shapes of each factor:

    - recency:        logarithmic growth (1 + log1p(days))
    - count_damping:  hyperbolic decay (1 / (1 + total))
    - failure_boost:  linear growth (1 + recent_fails)

    The product is always > 0, so it is safe to feed to random.choices.
    """
    if now is None:
        now = datetime.now(tz=UTC)

    if stats.last_reviewed_at is None:
        days_since_last_review = NEVER_REVIEWED_DAYS_SINCE_LAST_REVIEW
    else:
        days_since_last_review = max(
            (now - stats.last_reviewed_at).total_seconds() / _SECONDS_PER_DAY,
            0.0,
        )

    recency = 1.0 + math.log1p(days_since_last_review)
    count_damping = 1.0 / (1.0 + stats.total_reviews)
    failure_boost = 1.0 + stats.recent_failures

    return recency * count_damping * failure_boost


def select_next_exercise(
    application: ExerciseApplication,
    identifier: str | None = None,
    status: ReviewStatus = ReviewStatus.ALL,
    rng: random.Random | None = None,
    now: datetime | None = None,
) -> Exercise | None:
    """Pick the next exercise to review using weighted random selection.

    ``status`` filters candidates: ``ReviewStatus.NEW`` (never reviewed),
    ``ReviewStatus.REVIEWED`` (at least one review) or ``ReviewStatus.ALL``.
    Returns None when no exercise matches the filters.
    """
    if rng is None:
        rng = random.Random()

    candidates: list[Exercise] = []
    weights: list[float] = []

    for exercise in application.browse_exercises(identifier, status):
        assert exercise.uuid is not None
        stats = application.review_stats(exercise.uuid)

        candidates.append(exercise)
        weights.append(compute_weight(stats, now=now))

    if not candidates:
        return None

    return rng.choices(candidates, weights=weights, k=1)[0]
