import errno
import logging
import os
import shutil
import sqlite3
import tempfile
import zipfile
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from exercise_library.config import APP_NAME, DATABASE_NAME
from exercise_library.locking import application_lock
from exercise_library.paths import app_backup_dir_path, app_data_dir_path


class BackupError(Exception):
    pass


class SQLiteBackupError(Exception):
    pass


logger = logging.getLogger(__name__)

SQLITE_DATABASES_REL_PATHS: tuple[Path] = (Path(DATABASE_NAME),)

OTHER_REL_FILE_PATHS: tuple[Path, ...] = ()

BACKUP_REL_FILE_PATHS: tuple[Path, ...] = (
    *SQLITE_DATABASES_REL_PATHS,
    *OTHER_REL_FILE_PATHS,
)


def create_backup(output: Path | None = None) -> Path:
    logger.info("Starting Backup")

    return _create_backup(output)


def _create_backup(output: Path | None = None) -> Path:
    if not app_data_dir_path().is_dir():
        raise BackupError(
            f"Application data directory does not exist: {app_data_dir_path()}"
        )

    output = _ensure_output(output)

    with (
        application_lock(),
        tempfile.TemporaryDirectory(dir=(app_backup_dir_path())) as tmp_dir,
    ):
        staging_dir_path = Path(tmp_dir) / "staging"

        _copy_whitelisted_files(
            app_data_dir_path(),
            staging_dir_path,
            _sqlite_backup,
        )

        assert staging_dir_path.exists()

        temporary_archive_path = Path(tmp_dir) / "tmp_backup.zip"

        _write_zip(
            staging_dir_path,
            temporary_archive_path,
            APP_NAME,
        )

        assert temporary_archive_path.exists() and temporary_archive_path.is_file()

        _replace(temporary_archive_path, output)

    return output


def _replace(src: Path, dst: Path) -> None:
    try:
        os.replace(src, dst)
    except PermissionError as exc:
        raise BackupError(
            f"Could not save the archive to '{dst}': permission denied. "
            "Choose another location or close the file if it is currently open."
        ) from exc
    except OSError as exc:
        if exc.errno == errno.EXDEV:
            raise BackupError(
                "Could not save the backup because the selected destination "
                "is on a different filesystem. Please choose another location."
            ) from exc
        elif exc.errno == errno.ENOSPC:
            raise BackupError(
                "There isn't enough disk space to copy the file. "
                "Free some space and try again."
            ) from exc

        elif exc.errno == errno.EROFS:
            raise BackupError(
                "The destination is read-only. Choose a writable destination."
            ) from exc

        else:
            raise RuntimeError(
                "The file could not be copied because of an unexpected system error.",
            ) from exc


def _ensure_output(output: Path | None) -> Path:
    if output is None:
        timestamp = datetime.now(UTC).strftime("w%Y%m%dT%H%M%SZ")
        output = app_backup_dir_path() / (f"{APP_NAME}--backup--{timestamp}.zip")

    else:
        try:
            output = output.expanduser()
        except RuntimeError as exc:
            raise BackupError(
                f"Could not expand the output path '{output}'. "
                "Please provide an absolute path instead of using '~'."
            ) from exc

        output = output.resolve()

        if output.suffix.lower() != ".zip":
            output = output.with_suffix(".zip")

        if not output.parent.is_dir():
            raise BackupError(
                "Parent directory of provided output file does not exists\n"
                f"{output.parent}"
            )

    return output


def _copy_whitelisted_files(
    data_dir_path: Path,
    staging_dir_path: Path,
    sqlite_backup_fn: Callable[[Path, Path], None],
) -> None:

    assert all(not path.is_absolute() for path in BACKUP_REL_FILE_PATHS)

    src_dst: dict[Path, Path] = {
        (data_dir_path / rel_path): (staging_dir_path / rel_path)
        for rel_path in BACKUP_REL_FILE_PATHS
    }

    for src, dst in src_dst.items():
        if not src.exists():
            raise BackupError(f"Required backup file does not exist: {src}")

        if src.is_symlink():
            raise BackupError(f"Symlinks are not supported in backups: {src}")

        if not src.is_file():
            raise BackupError(f"Backup entry is not a regular file: {src}")

        dst.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if src.resolve() == dst.resolve():
            raise RuntimeError()

        if Path(src.name) in SQLITE_DATABASES_REL_PATHS:
            sqlite_backup_fn(
                src,
                dst,
            )
        else:
            try:
                shutil.copy2(src, dst)

            except PermissionError as exc:
                raise BackupError(
                    "The file could not be copied because access was denied. "
                    "Check your permissions or choose a different destination."
                ) from exc

            except OSError as exc:
                if exc.errno == errno.ENOSPC:
                    raise BackupError(
                        "There isn't enough disk space to copy the file. "
                        "Free some space and try again."
                    ) from exc

                if exc.errno == errno.EROFS:
                    raise BackupError(
                        "The destination is read-only. Choose a writable destination."
                    ) from exc

                else:
                    raise RuntimeError(
                        "The file could not be copied because of an unexpected "
                        "system error.",
                    ) from exc


def _sqlite_backup(src: Path, dst: Path) -> None:
    src = src.resolve()
    dst = dst.resolve()

    # Caller invariants.
    if src == dst:
        raise ValueError(f"'{src}' and '{dst}' must differ.")

    if not src.is_file():
        raise ValueError(f"Source database '{src}' does not exist.")

    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise SQLiteBackupError("Could not prepare the backup.") from exc

    src_uri = f"{src.as_uri()}?mode=ro"

    try:
        src_connection = sqlite3.connect(src_uri, uri=True)
    except sqlite3.Error as exc:
        raise SQLiteBackupError(
            "Could not open the database for backup.",
        ) from exc

    try:
        try:
            dst_connection = sqlite3.connect(dst)
        except sqlite3.Error as exc:
            raise SQLiteBackupError("Could not prepare the backup.") from exc

        try:
            src_connection.backup(
                dst_connection,
                pages=1,
                sleep=0.5,
            )
            dst_connection.commit()
        except sqlite3.Error as exc:
            raise SQLiteBackupError("Could not back up the database.") from exc
        finally:
            dst_connection.close()

    finally:
        src_connection.close()


def _write_zip(
    staging_directory: Path,
    output: Path,
    base_internal_dir_name: str,
) -> None:
    with zipfile.ZipFile(
        output,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        for path in staging_directory.rglob("*"):
            # all files are under app_name/ inside the zip
            archive_name = Path(base_internal_dir_name) / path.relative_to(
                staging_directory
            )

            if path.is_dir():
                # Preserve empty directories.
                if not any(path.iterdir()):
                    archive.writestr(
                        archive_name.as_posix() + "/",
                        "",
                    )
            else:
                archive.write(
                    path,
                    arcname=archive_name.as_posix(),
                )
