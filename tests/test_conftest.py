from pathlib import Path

from exercise_library.paths import app_data_dir_path


def test_data_dir_is_isolated(tmp_path: Path) -> None:
    path = app_data_dir_path()

    assert path == tmp_path / "exercise-library"
    assert path.is_dir()

    test_file = path / "test.txt"
    test_file.write_text("test", encoding="utf-8")

    assert test_file.read_text(encoding="utf-8") == "test"
