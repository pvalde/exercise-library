import hashlib
import re
from pathlib import Path

_MEDIA_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

_MEDIA_TYPES_BY_EXTENSION: dict[str, str] = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
}


def is_valid_media_name(name: str) -> bool:
    """Return whether ``name`` is a safe, referenceable media file name."""
    return bool(_MEDIA_NAME_PATTERN.fullmatch(name))


def media_type_for_name(name: str) -> str | None:
    """Return the media type for a supported extension, or None."""
    return _MEDIA_TYPES_BY_EXTENSION.get(Path(name).suffix.lower())


def hash_file(path: Path) -> str:
    """Return the hex-encoded SHA-256 digest of the file at ``path``."""
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()
