from pathlib import Path

import platformdirs

from exercise_library.config import APP_NAME


def data_dir() -> Path:
    path = platformdirs.user_data_path(APP_NAME)
    path.mkdir(parents=True, exist_ok=True)
    return path


def log_file() -> Path:
    dir_path = platformdirs.user_log_path(APP_NAME)
    dir_path.mkdir(parents=True, exist_ok=True)
    file_path = dir_path / f"{APP_NAME}.log"
    return file_path
