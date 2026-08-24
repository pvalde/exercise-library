import pytest

from exercise_library.application import ExerciseApplication
from exercise_library.database import initialize
from exercise_library.repository import ExerciseRepository


@pytest.fixture
def application() -> ExerciseApplication:
    connection = initialize()
    repository = ExerciseRepository(connection)
    return ExerciseApplication(repository)
