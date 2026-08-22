from pathlib import Path

import pytest

from exercise_library.config import APP_NAME
from exercise_library.paths import data_dir


def test_data_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:

    path = data_dir()

    assert path == tmp_path / APP_NAME
    assert path.is_dir()
