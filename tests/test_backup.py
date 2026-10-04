import os
import sqlite3
import tempfile
import zipfile
from collections.abc import Callable
from pathlib import Path
from unittest.mock import Mock

import pytest

import exercise_library.backup as backup
from exercise_library.config import APP_NAME
from exercise_library.database import initialize
from exercise_library.paths import app_backup_dir_path, app_data_dir_path


@pytest.fixture
def mock_write_zip(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def fake_write_zip(staging_directory: Path, output: Path) -> None:
        zipfile.ZipFile(output)

    monkeypatch.setattr(backup, "_write_zip", Mock(side_effect=fake_write_zip))


@pytest.fixture
def mock_copy_whitelisted_files(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fake_copy_whitelisted_files(
        data_directory: Path, staging_directory: Path
    ) -> None:
        staging_directory.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(
        backup, "_copy_whitelisted_files", Mock(side_effect=fake_copy_whitelisted_files)
    )


@pytest.fixture
def mock_os(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(backup, "os", Mock())


# _create_backup ---------------------------------------------------------------


def test_create_backup_raises_if_no_data_dir(monkeypatch: pytest.MonkeyPatch) -> None:
    data_directory = Path("nonexistent-dir")
    monkeypatch.setattr(backup, "app_data_dir_path", Mock(return_value=data_directory))

    error_msg = f"Application data directory does not exist: {data_directory}"

    with pytest.raises(backup.BackupError, match=error_msg):
        backup._create_backup()


def test_replace(tmp_path: Path) -> None:
    src = tmp_path / "src"
    dst = tmp_path / "dst"

    src.write_text("content")

    backup._replace(src, dst)

    assert not src.exists()
    assert dst.read_text() == "content"


def test_replace_if_permission_denied_raises_backup_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    src = tmp_path / "src"
    dst = tmp_path / "dst"

    def fake_replace(src: Path, dst: Path) -> None:
        raise PermissionError("permission denied")

    monkeypatch.setattr(os, "replace", fake_replace)

    with pytest.raises(
        backup.BackupError,
        match="permission denied",
    ):
        backup._replace(src, dst)


# _ensure_output ---------------------------------------------------------------


def test_ensure_output_default_output_is_under_data_dir(
    tmp_path: Path,
    mock_copy_whitelisted_files: Callable[[None], None],
    mock_write_zip: Callable[[None], None],
    mock_os: Callable[[None], None],
) -> None:

    assert backup._ensure_output(None).parent == app_backup_dir_path()


def test_ensure_output_with_absolute_output_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "backup.zip"

    result = backup._ensure_output(output)

    assert result == output
    assert result.is_absolute()


def test_ensure_output_raises_if_home_directory_cannot_be_determined(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = Path("~/backup.zip")

    monkeypatch.setattr(
        Path,
        "expanduser",
        Mock(side_effect=RuntimeError("Could not determine home directory")),
    )

    with pytest.raises(
        backup.BackupError,
        match="Could not expand the output path",
    ):
        backup._ensure_output(output)


def test_ensure_output_adds_suffix_if_provided_file_does_not_have_it(
    tmp_path: Path,
) -> None:
    assert backup._ensure_output(tmp_path / "myfile") == (tmp_path / "myfile.zip")


def test_ensure_output_raises_if_parent_dir_provided_file_does_not_exists() -> None:
    output_file = Path("/non/existent/path/backup.zip")

    with pytest.raises(
        backup.BackupError,
        match="Parent directory of provided output file does not exists\n"
        + f"{output_file.parent}",
    ):
        backup._ensure_output(output_file)


# _copy_whitelisted_files ------------------------------------------------------


def test_copy_whitelisted_files_backup_paths_are_relative(tmp_path: Path) -> None:
    assert all(not path.is_absolute() for path in backup.BACKUP_REL_FILE_PATHS)


def test_copy_whitelisted_files_raises_if_required_file_does_not_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:

    app_data_dir = app_data_dir_path()

    with pytest.raises(
        backup.BackupError,
        match="Required backup file does not exist:"
        + f" {app_data_dir / 'non-existent-file'}",
    ):
        BACKUP_REL_FILE_PATHS: tuple[Path, ...] = (Path("non-existent-file"),)
        monkeypatch.setattr(backup, "BACKUP_REL_FILE_PATHS", BACKUP_REL_FILE_PATHS)

        backup._copy_whitelisted_files(
            app_data_dir,
            tmp_path / "staging",
            Mock(),
        )

    with tempfile.NamedTemporaryFile(dir=app_data_dir) as tf:
        tf_path: Path = Path(tf.name)
        tf_name_path = Path(tf_path.name)
        BACKUP_REL_FILE_PATHS = (tf_name_path, (Path("non-existent-file")))

        monkeypatch.setattr(backup, "BACKUP_REL_FILE_PATHS", BACKUP_REL_FILE_PATHS)
        with pytest.raises(
            backup.BackupError,
            match="Required backup file does not exist:"
            + f" {app_data_dir / 'non-existent-file'}",
        ):
            backup._copy_whitelisted_files(
                app_data_dir,
                tmp_path / "staging",
                Mock(),
            )


def test_copy_whitelisted_files_raises_if_target_file_is_simlink(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    app_data_dir = app_data_dir_path()

    with tempfile.NamedTemporaryFile() as tf:
        tf_path: Path = Path(tf.name)
        symlink_path = app_data_dir / "symlink"
        os.symlink(tf_path, symlink_path)

        monkeypatch.setattr(backup, "BACKUP_REL_FILE_PATHS", (Path(symlink_path.name),))

        with pytest.raises(
            backup.BackupError,
            match=f"Symlinks are not supported in backups: {symlink_path}",
        ):
            backup._copy_whitelisted_files(
                app_data_dir,
                tmp_path / "staging",
                Mock(),
            )


def test_copy_whitelisted_file_raises_if_target_file_is_not_regular_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app_data_dir = app_data_dir_path()

    with tempfile.TemporaryDirectory(dir=app_data_dir) as dir:
        dir_path = Path(dir)
        dir_name = dir_path.name
        monkeypatch.setattr(backup, "BACKUP_REL_FILE_PATHS", (Path(dir_name),))

        with pytest.raises(
            backup.BackupError,
            match=f"Backup entry is not a regular file: {dir_path}",
        ):
            backup._copy_whitelisted_files(
                app_data_dir,
                tmp_path / "staging",
                Mock(),
            )


def test_copy_whitelisted_file_calls_sqlite_backup_fn_and_shutil_copy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # create a db
    app_data_dir = app_data_dir_path()
    db_path = app_data_dir / "db.sqlite3"
    sqlite3.connect(db_path)
    assert db_path.exists()

    # create a file
    file_path = app_data_dir / "file"
    file_path.touch()
    assert file_path.is_file()
    assert file_path.exists()

    monkeypatch.setattr(backup, "SQLITE_DATABASES_REL_PATHS", (Path(db_path.name),))

    monkeypatch.setattr(
        backup,
        "BACKUP_REL_FILE_PATHS",
        (Path(db_path.name), Path(file_path.name)),
    )

    fake_shutil = Mock()

    monkeypatch.setattr(
        backup,
        "shutil",
        fake_shutil,
    )

    fake_sqlite_backup_fn = Mock()

    backup._copy_whitelisted_files(
        app_data_dir,
        app_backup_dir_path() / "staging",
        fake_sqlite_backup_fn,
    )

    staging_db_path = app_backup_dir_path() / "staging" / db_path.name
    fake_sqlite_backup_fn.assert_called_with(db_path, staging_db_path)

    staging_file_path = app_backup_dir_path() / "staging" / file_path.name
    fake_shutil.copy2.assert_called_once_with(file_path, staging_file_path)


def test_copy_whitelisted_files_creates_staging_dst_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # create a db
    app_data_dir = app_data_dir_path()
    db_path = app_data_dir / "db.sqlite3"
    sqlite3.connect(db_path)
    assert db_path.exists()

    # create a file
    file_path = app_data_dir / "file"
    file_path.touch()
    assert file_path.is_file()
    assert file_path.exists()

    monkeypatch.setattr(backup, "SQLITE_DATABASES_REL_PATHS", (Path(db_path.name),))

    monkeypatch.setattr(
        backup,
        "BACKUP_REL_FILE_PATHS",
        (Path(db_path.name), Path(file_path.name)),
    )

    backup._copy_whitelisted_files(
        app_data_dir,
        app_backup_dir_path() / "staging",
        backup._sqlite_backup,
    )

    staging_db_path = app_backup_dir_path() / "staging" / db_path.name
    assert staging_db_path.exists()
    assert staging_db_path.is_file()

    staging_file_path = app_backup_dir_path() / "staging" / file_path.name
    assert staging_file_path.exists()
    assert staging_file_path.is_file()


# _copy_whitelisted_files - directories ----------------------------------------


@pytest.fixture
def no_file_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(backup, "BACKUP_REL_FILE_PATHS", ())


def test_copy_whitelisted_dirs_backup_paths_are_relative() -> None:
    assert all(not path.is_absolute() for path in backup.BACKUP_REL_DIR_PATHS)


def test_copy_whitelisted_dirs_skips_missing_directory(
    tmp_path: Path,
    no_file_paths: None,
) -> None:
    app_data_dir = app_data_dir_path()
    staging = tmp_path / "staging"

    backup._copy_whitelisted_files(app_data_dir, staging, Mock())

    assert not (staging / "media").exists()


def test_copy_whitelisted_dirs_copies_media_files(
    tmp_path: Path,
    no_file_paths: None,
) -> None:
    app_data_dir = app_data_dir_path()
    media_dir = app_data_dir / "media"
    (media_dir / "nested").mkdir(parents=True)
    (media_dir / "cat.png").write_bytes(b"cat")
    (media_dir / "nested" / "dog.jpg").write_bytes(b"dog")

    staging = tmp_path / "staging"

    backup._copy_whitelisted_files(app_data_dir, staging, Mock())

    assert (staging / "media" / "cat.png").read_bytes() == b"cat"
    assert (staging / "media" / "nested" / "dog.jpg").read_bytes() == b"dog"


def test_copy_whitelisted_dirs_raises_if_media_is_symlink(
    tmp_path: Path,
    no_file_paths: None,
) -> None:
    app_data_dir = app_data_dir_path()
    target = tmp_path / "target"
    target.mkdir()
    os.symlink(target, app_data_dir / "media")

    with pytest.raises(
        backup.BackupError,
        match="Symlinks are not supported in backups:",
    ):
        backup._copy_whitelisted_files(app_data_dir, tmp_path / "staging", Mock())


def test_copy_whitelisted_dirs_raises_if_entry_is_a_file(
    tmp_path: Path,
    no_file_paths: None,
) -> None:
    app_data_dir = app_data_dir_path()
    (app_data_dir / "media").write_text("not a directory")

    with pytest.raises(
        backup.BackupError,
        match="Backup entry is not a directory:",
    ):
        backup._copy_whitelisted_files(app_data_dir, tmp_path / "staging", Mock())


def test_copy_whitelisted_dirs_raises_if_contained_file_is_symlink(
    tmp_path: Path,
    no_file_paths: None,
) -> None:
    app_data_dir = app_data_dir_path()
    media_dir = app_data_dir / "media"
    media_dir.mkdir(parents=True)

    target = tmp_path / "target"
    target.write_bytes(b"target")
    os.symlink(target, media_dir / "link.png")

    with pytest.raises(
        backup.BackupError,
        match="Symlinks are not supported in backups:",
    ):
        backup._copy_whitelisted_files(app_data_dir, tmp_path / "staging", Mock())


# _sqlite_backup ---------------------------------------------------------------


def _create_database(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE test (
                id INTEGER PRIMARY KEY,
                value TEXT NOT NULL
            )
            """,
        )
        connection.execute(
            "INSERT INTO test (value) VALUES (?)",
            ("hello",),
        )


def test_sqlite_backup_if_src_dst_equal_raises(tmp_path: Path) -> None:
    with tempfile.NamedTemporaryFile(dir=tmp_path) as tf, pytest.raises(ValueError):
        tf_path = Path(tf.name)
        backup._sqlite_backup(tf_path, tf_path)


def test_sqlite_backup_if_src_is_not_file_raises(tmp_path: Path) -> None:
    with (
        tempfile.TemporaryDirectory(dir=tmp_path) as td_path,
        pytest.raises(ValueError),
    ):
        backup._sqlite_backup(Path(td_path), tmp_path / "dst")


def test_sqlite_backup_copies_database(tmp_path: Path) -> None:
    src = tmp_path / "src.sqlite"
    dst = tmp_path / "dst.sqlite"

    _create_database(src)

    backup._sqlite_backup(src, dst)

    assert dst.is_file()

    with sqlite3.connect(dst) as connection:
        row = connection.execute(
            "SELECT value FROM test WHERE id = 1",
        ).fetchone()

    assert row == ("hello",)


def test_sqlite_backup_creates_destination_parent_directories(
    tmp_path: Path,
) -> None:
    src = tmp_path / "src.sqlite"
    dst = tmp_path / "nested" / "backup" / "dst.sqlite"

    _create_database(src)

    backup._sqlite_backup(src, dst)

    assert dst.is_file()


def test_sqlite_backup_overwrites_existing_destination(
    tmp_path: Path,
) -> None:
    src = tmp_path / "src.sqlite"
    dst = tmp_path / "dst.sqlite"

    _create_database(src)

    with sqlite3.connect(dst) as connection:
        connection.execute(
            "CREATE TABLE old_table (value TEXT NOT NULL)",
        )
        connection.execute(
            "INSERT INTO old_table (value) VALUES (?)",
            ("old",),
        )

    backup._sqlite_backup(src, dst)

    with sqlite3.connect(dst) as connection:
        value = connection.execute(
            "SELECT value FROM test WHERE id = 1",
        ).fetchone()

        old_table = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = 'old_table'
            """,
        ).fetchone()

    assert value == ("hello",)
    assert old_table is None


def test_sqlite_backup_if_destination_parent_cannot_be_created(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src = tmp_path / "src.sqlite"
    dst = tmp_path / "nested" / "dst.sqlite"

    _create_database(src)

    def fake_mkdir(
        self: Path,
        mode: int = 0o777,
        *,
        parents: bool = False,
        exist_ok: bool = False,
    ) -> None:
        raise OSError("permission denied")

    monkeypatch.setattr(Path, "mkdir", fake_mkdir)

    with pytest.raises(
        backup.SQLiteBackupError,
        match="Could not prepare the backup",
    ):
        backup._sqlite_backup(src, dst)


def test_sqlite_backup_if_source_cannot_be_opened(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src = tmp_path / "src.sqlite"
    dst = tmp_path / "dst.sqlite"

    src.touch()

    fake_sqlite3 = Mock()
    fake_sqlite3.Error = sqlite3.Error

    def fake_connect(
        database: str | Path,
        *,
        uri: bool = False,
    ) -> sqlite3.Connection:
        raise sqlite3.OperationalError("cannot open database")

    fake_sqlite3.connect.side_effect = fake_connect

    monkeypatch.setattr(backup, "sqlite3", fake_sqlite3)

    with pytest.raises(
        backup.SQLiteBackupError,
        match="Could not open the database for backup",
    ):
        backup._sqlite_backup(src, dst)


# _write_zip -------------------------------------------------------------------


def test_write_zip_creates_archive(tmp_path: Path) -> None:
    with tempfile.TemporaryDirectory(dir=tmp_path) as td_path:
        staging = Path(td_path)

        output = tmp_path / "output.zip"

        backup._write_zip(staging, output, "app_name")

        assert output.exists()
        assert zipfile.is_zipfile(output)


def test_write_zip_includes_regular_files(tmp_path: Path) -> None:
    DUMMY_APP_NAME = "app_name"

    with tempfile.TemporaryDirectory(dir=tmp_path) as td_path:
        staging = Path(td_path)

        (staging / "hello.txt").write_text("hello")
        (staging / "data.json").write_text('{"foo": "bar"}')

        output = tmp_path / "output.zip"

        backup._write_zip(staging, output, DUMMY_APP_NAME)

        with zipfile.ZipFile(output) as archive:
            assert set(archive.namelist()) == {
                f"{DUMMY_APP_NAME}/hello.txt",
                f"{DUMMY_APP_NAME}/data.json",
            }

            assert archive.read(f"{DUMMY_APP_NAME}/hello.txt") == b"hello"
            assert archive.read(f"{DUMMY_APP_NAME}/data.json") == b'{"foo": "bar"}'


def test_write_zip_preserves_nested_directory_structure(
    tmp_path: Path,
) -> None:
    DUMMY_APP_NAME = "app_name"

    with tempfile.TemporaryDirectory(dir=tmp_path) as td_path:
        staging = Path(td_path)

        deep = staging / "a" / "b" / "c"
        deep.mkdir(parents=True)

        (deep / "file.txt").touch()
        (deep / "file.txt").write_text("content")

        output = tmp_path / "output.zip"

        backup._write_zip(staging, output, DUMMY_APP_NAME)

        with zipfile.ZipFile(output) as archive:
            assert archive.namelist() == [
                f"{DUMMY_APP_NAME}/a/b/c/file.txt",
            ]

            assert archive.read(f"{DUMMY_APP_NAME}/a/b/c/file.txt") == b"content"


def test_write_zip_preserves_empty_directories(tmp_path: Path) -> None:
    DUMMY_APP_NAME = "app_name"

    with tempfile.TemporaryDirectory(dir=tmp_path) as td_path:
        staging = Path(td_path)

        (staging / "empty").mkdir(parents=True)
        (staging / "nested" / "empty").mkdir(parents=True)

        output = tmp_path / "output.zip"

        backup._write_zip(staging, output, DUMMY_APP_NAME)

        with zipfile.ZipFile(output) as archive:
            assert set(archive.namelist()) == {
                f"{DUMMY_APP_NAME}/empty/",
                f"{DUMMY_APP_NAME}/nested/empty/",
            }


def test_write_zip_does_not_explicitly_store_non_empty_directories(
    tmp_path: Path,
) -> None:
    DUMMY_APP_NAME = "app_name"
    with tempfile.TemporaryDirectory(dir=tmp_path) as td_path:
        staging = Path(td_path)

        directory = staging / "non-empty"
        directory.mkdir()
        (directory / "file.txt").write_text("content")

        output = tmp_path / "output.zip"

        backup._write_zip(staging, output, DUMMY_APP_NAME)

        with zipfile.ZipFile(output) as archive:
            names = set(archive.namelist())

        assert f"{DUMMY_APP_NAME}/non-empty/" not in names
        assert f"{DUMMY_APP_NAME}/non-empty/file.txt" in names


def test_write_zip_prefixes_every_entry_with_app_name(
    tmp_path: Path,
) -> None:
    DUMMY_APP_NAME = "app_name"

    with tempfile.TemporaryDirectory(dir=tmp_path) as td_path:
        staging = Path(td_path)
        (staging / "file.txt").touch()
        (staging / "file.txt").write_text("content")
        (staging / "empty").mkdir(parents=True)
        (staging / "nested" / "file.txt").parent.mkdir()
        (staging / "nested" / "file.txt").write_text("nested")

        output = tmp_path / "output.zip"

        backup._write_zip(staging, output, DUMMY_APP_NAME)

        with zipfile.ZipFile(output) as archive:
            names = archive.namelist()

        assert all(name.startswith(f"{DUMMY_APP_NAME}/") for name in names)


def test_write_zip_uses_posix_paths(tmp_path: Path) -> None:
    DUMMY_APP_NAME = "app_name"
    with tempfile.TemporaryDirectory(dir=tmp_path) as td_path:
        staging = Path(td_path)

        nested = staging / "nested" / "directory"
        nested.mkdir(parents=True)
        (nested / "file.txt").write_text("content")

        output = tmp_path / "output.zip"

        backup._write_zip(staging, output, DUMMY_APP_NAME)

        with zipfile.ZipFile(output) as archive:
            names = archive.namelist()

        assert f"{DUMMY_APP_NAME}/nested/directory/file.txt" in names
        assert all("\\" not in name for name in names)


def test_write_zip_preserves_binary_file_contents(
    tmp_path: Path,
) -> None:
    DUMMY_APP_NAME = "app_name"
    with tempfile.TemporaryDirectory(dir=tmp_path) as td_path:
        staging = Path(td_path)

        content = bytes(range(256))
        (staging / "binary.bin").touch()
        (staging / "binary.bin").write_bytes(content)

        output = tmp_path / "output.zip"

        backup._write_zip(staging, output, DUMMY_APP_NAME)

        with zipfile.ZipFile(output) as archive:
            assert archive.read(f"{DUMMY_APP_NAME}/binary.bin") == content


def test_write_zip_handles_unicode_and_spaces_in_filenames(
    tmp_path: Path,
) -> None:
    DUMMY_APP_NAME = "app_name"
    with tempfile.TemporaryDirectory(dir=tmp_path) as td_path:
        staging = Path(td_path)

        media = staging / "media"
        media.mkdir()

        filename = "my cute cat — café.jpg"
        content = b"fake image"

        (media / filename).write_bytes(content)

        output = tmp_path / "output.zip"

        backup._write_zip(staging, output, DUMMY_APP_NAME)

        with zipfile.ZipFile(output) as archive:
            archive_path = f"{DUMMY_APP_NAME}/media/{filename}"

            assert archive_path in archive.namelist()
            assert archive.read(archive_path) == content


def test_write_zip_handles_multiple_media_files(
    tmp_path: Path,
) -> None:
    DUMMY_APP_NAME = "app_name"
    with tempfile.TemporaryDirectory(dir=tmp_path) as td_path:
        staging = Path(td_path)
        media = staging / "media"
        media.mkdir()

        files = {
            "cat.jpg": b"cat",
            "dog.png": b"dog",
            "diagram.webp": b"diagram",
        }

        for filename, content in files.items():
            (media / filename).write_bytes(content)

        output = tmp_path / "output.zip"

        backup._write_zip(staging, output, DUMMY_APP_NAME)

        with zipfile.ZipFile(output) as archive:
            for filename, content in files.items():
                archive_path = f"{DUMMY_APP_NAME}/media/{filename}"

                assert archive_path in archive.namelist()
                assert archive.read(archive_path) == content


def test_write_zip_does_not_modify_staging_directory(
    tmp_path: Path,
) -> None:
    DUMMY_APP_NAME = "app_name"
    with tempfile.TemporaryDirectory(dir=tmp_path) as td_path:
        staging = Path(td_path)

        (staging / "file.txt").write_text("hello")
        (staging / "empty").mkdir()
        (staging / "nested").mkdir()
        (staging / "nested" / "file.txt").write_text("nested")

        before = {
            path.relative_to(staging): ("dir" if path.is_dir() else path.read_bytes())
            for path in staging.rglob("*")
        }

        output = tmp_path / "output.zip"

        backup._write_zip(staging, output, DUMMY_APP_NAME)

        after = {
            path.relative_to(staging): ("dir" if path.is_dir() else path.read_bytes())
            for path in staging.rglob("*")
        }

        assert after == before


def test_write_zip_empty_staging_directory(
    tmp_path: Path,
) -> None:
    DUMMY_APP_NAME = "app_name"
    with tempfile.TemporaryDirectory(dir=tmp_path) as td_path:
        staging = Path(td_path)

        output = tmp_path / "output.zip"

        backup._write_zip(staging, output, DUMMY_APP_NAME)

        with zipfile.ZipFile(output) as archive:
            assert archive.namelist() == []


def test_write_zip_multiple_levels_and_empty_directories(
    tmp_path: Path,
) -> None:

    DUMMY_APP_NAME = "app_name"
    with tempfile.TemporaryDirectory(dir=tmp_path) as td_path:
        staging = Path(td_path)
        (staging / "media" / "images").mkdir(parents=True)
        (staging / "media" / "images" / "cat.jpg").write_bytes(b"cat")

        (staging / "media" / "audio").mkdir(parents=True)
        (staging / "media" / "audio" / "empty").mkdir()

        (staging / "documents" / "empty").mkdir(parents=True)

        (staging / "documents" / "readme.md").write_text("# Hello")

        output = tmp_path / "output.zip"

        backup._write_zip(staging, output, DUMMY_APP_NAME)

        with zipfile.ZipFile(output) as archive:
            assert set(archive.namelist()) == {
                f"{DUMMY_APP_NAME}/media/images/cat.jpg",
                f"{DUMMY_APP_NAME}/media/audio/empty/",
                f"{DUMMY_APP_NAME}/documents/empty/",
                f"{DUMMY_APP_NAME}/documents/readme.md",
            }


def test_write_zip_can_be_read_after_reopening_archive(
    tmp_path: Path,
) -> None:
    DUMMY_APP_NAME = "app_name"
    with tempfile.TemporaryDirectory(dir=tmp_path) as td_path:
        staging = Path(td_path)

        (staging / "hello.txt").write_text("hello")

        output = tmp_path / "output.zip"

        backup._write_zip(staging, output, DUMMY_APP_NAME)

        # Close/reopen independently of _write_zip's context manager.
        with zipfile.ZipFile(output, mode="r") as archive:
            assert archive.testzip() is None
            assert archive.read(f"{DUMMY_APP_NAME}/hello.txt") == b"hello"


# create_backup -----------------------------------------------------------------


def test_create_backup_includes_media(tmp_path: Path) -> None:
    initialize()

    media_dir = app_data_dir_path() / "media"
    (media_dir / "nested").mkdir(parents=True)
    (media_dir / "diagram.png").write_bytes(b"image")
    (media_dir / "nested" / "photo.jpg").write_bytes(b"photo")

    output = tmp_path / "backup.zip"

    backup.create_backup(output)

    with zipfile.ZipFile(output) as archive:
        names = set(archive.namelist())

        assert f"{APP_NAME}/media/diagram.png" in names
        assert f"{APP_NAME}/media/nested/photo.jpg" in names
        assert archive.read(f"{APP_NAME}/media/diagram.png") == b"image"


def test_create_backup_without_media(tmp_path: Path) -> None:
    initialize()

    output = tmp_path / "backup.zip"

    backup.create_backup(output)

    with zipfile.ZipFile(output) as archive:
        assert not any(
            name.startswith(f"{APP_NAME}/media/") for name in archive.namelist()
        )
