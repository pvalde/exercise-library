import dataclasses
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from uuid import uuid7

import pytest

from exercise_library.models import Exercise, Review, ReviewRating, ReviewSummary


def test_exercise() -> None:
    exercise = Exercise(
        prompt="What is the derivative of x^2?",
        answer="2x",
    )

    assert exercise.prompt == "What is the derivative of x^2?"
    assert exercise.answer == "2x"


def test_review_rating_maps_to_db_integers() -> None:
    assert ReviewRating.WRONG.value == 0
    assert ReviewRating.HARD.value == 1
    assert ReviewRating.GOOD.value == 2
    assert ReviewRating.EASY.value == 3

    assert int(ReviewRating.GOOD) == 2
    assert ReviewRating(2) is ReviewRating.GOOD
    assert ReviewRating(0) is ReviewRating.WRONG


def test_review() -> None:

    review_uuid = uuid7()
    exercise_uuid = uuid7()
    reviewed_at = datetime.now(tz=UTC)

    review = Review(
        uuid=review_uuid,
        exercise_uuid=exercise_uuid,
        reviewed_at=reviewed_at,
        rating=ReviewRating.GOOD,
    )

    assert review.uuid == review_uuid
    assert review.exercise_uuid == exercise_uuid
    assert review.reviewed_at == reviewed_at
    assert review.rating is ReviewRating.GOOD


def test_review_is_immutable() -> None:
    review = Review(
        uuid=uuid7(),
        exercise_uuid=uuid7(),
        reviewed_at=datetime.now(tz=UTC),
        rating=ReviewRating.EASY,
    )

    with pytest.raises(FrozenInstanceError):
        del review.rating

    updated = dataclasses.replace(review, rating=ReviewRating.WRONG)

    assert review.rating is ReviewRating.EASY
    assert updated.rating is ReviewRating.WRONG
    assert updated is not review


def test_review_summary() -> None:

    exercise_uuid = uuid7()
    now = datetime.now(tz=UTC)

    summary = ReviewSummary(
        exercise_uuid=exercise_uuid,
        total_reviews=42,
        failures=7,
        updated_at=now,
        first_reviewed_at=now,
    )

    assert summary.exercise_uuid == exercise_uuid
    assert summary.total_reviews == 42
    assert summary.failures == 7
    assert summary.updated_at == now
    assert summary.first_reviewed_at == now


def test_review_summary_without_first_review() -> None:

    summary = ReviewSummary(
        exercise_uuid=uuid7(),
        total_reviews=0,
        failures=0,
        updated_at=datetime.now(tz=UTC),
    )

    assert summary.first_reviewed_at is None
