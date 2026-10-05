from pathlib import Path

import platformdirs
import pytest

from exercise_library.application import ExerciseApplication
from exercise_library.config import APP_NAME
from exercise_library.database import initialize
from exercise_library.repository import (
    ExerciseRepository,
    MediaRepository,
    ReviewRepository,
)


@pytest.fixture(scope="function", autouse=True)
def isolate_user_data(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        platformdirs,
        "user_data_path",
        lambda _: tmp_path / APP_NAME,
    )


@pytest.fixture
def application() -> ExerciseApplication:
    connection = initialize()
    repository = ExerciseRepository(connection)
    media_repository = MediaRepository(connection)
    review_repository = ReviewRepository(connection)
    return ExerciseApplication(repository, media_repository, review_repository)
