from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum
from uuid import UUID


class ReviewRating(IntEnum):
    WRONG = 0
    HARD = 1
    GOOD = 2
    EASY = 3

    @property
    def is_failure(self) -> bool:
        """Whether this rating counts as a failure in review statistics."""
        return self in (ReviewRating.WRONG, ReviewRating.HARD)


@dataclass(frozen=True)
class Exercise:
    prompt: str
    answer: str
    identifier: str | None = None
    uuid: UUID | None = None


@dataclass(frozen=True)
class Media:
    name: str
    media_type: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class Review:
    uuid: UUID
    exercise_uuid: UUID
    reviewed_at: datetime
    rating: ReviewRating


@dataclass(frozen=True)
class ArchivedReviewStats:
    exercise_uuid: UUID
    total_reviews: int
    failures: int
    updated_at: datetime
    first_reviewed_at: datetime | None = None
