from pathlib import Path

import pytest

from exercise_library.config import APP_NAME
from exercise_library.paths import app_backup_dir_path, app_data_dir_path


def test_data_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:

    path = app_data_dir_path()

    assert path == tmp_path / APP_NAME
    assert path.is_dir()


def test_backup_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:

    path = app_backup_dir_path()

    assert path == tmp_path / APP_NAME / "backups"
    assert path.is_dir()
