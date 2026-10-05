import pytest

from exercise_library.application import ExerciseApplication
from exercise_library.database import initialize
from exercise_library.repository import (
    ExerciseRepository,
    MediaRepository,
    ReviewRepository,
)


@pytest.fixture
def application() -> ExerciseApplication:
    connection = initialize()
    repository = ExerciseRepository(connection)
    media_repository = MediaRepository(connection)
    review_repository = ReviewRepository(connection)
    return ExerciseApplication(repository, media_repository, review_repository)
