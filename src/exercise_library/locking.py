from collections.abc import Generator
from contextlib import contextmanager

from filelock import FileLock, Timeout

from exercise_library.config import APP_NAME
from exercise_library.paths import runtime_path


class ApplicationLockTimeout(TimeoutError):
    """The application lock could not be acquired before the timeout."""


@contextmanager
def application_lock(timeout: float = 30) -> Generator[None]:

    lock_path = runtime_path() / f".{APP_NAME}.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    lock = FileLock(str(lock_path))

    try:
        lock.acquire(timeout=timeout)
    except Timeout as exc:
        raise ApplicationLockTimeout(
            f"{APP_NAME} is already running or its data is locked",
            f"(timeout: {timeout}s).",
        ) from exc

    try:
        yield
    finally:
        lock.release()
