from pathlib import Path

import platformdirs

from exercise_library.config import APP_NAME


def data_dir() -> Path:
    path = platformdirs.user_data_path(APP_NAME)
    path.mkdir(parents=True, exist_ok=True)
    return path
