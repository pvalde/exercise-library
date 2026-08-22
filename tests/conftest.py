from pathlib import Path

import platformdirs
import pytest

from exercise_library.config import APP_NAME


@pytest.fixture(scope="function", autouse=True)
def isolate_user_data(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        platformdirs,
        "user_data_path",
        lambda _: tmp_path / APP_NAME,
    )
