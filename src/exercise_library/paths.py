from pathlib import Path

import platformdirs

from exercise_library.config import APP_NAME, MEDIA_DIR_NAME


def app_data_dir_path() -> Path:
    path = platformdirs.user_data_path(APP_NAME)
    path.mkdir(parents=True, exist_ok=True)
    return path


def media_dir_path() -> Path:
    path = app_data_dir_path() / MEDIA_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def app_backup_dir_path() -> Path:
    path = app_data_dir_path() / "backups"
    path.mkdir(parents=True, exist_ok=True)
    return path


def log_file_path() -> Path:
    dir_path = platformdirs.user_log_path(APP_NAME)
    dir_path.mkdir(parents=True, exist_ok=True)
    file_path = dir_path / f"{APP_NAME}.log"
    return file_path


def runtime_path() -> Path:
    return platformdirs.user_runtime_path(APP_NAME)
