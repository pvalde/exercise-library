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

_IMAGE_REFERENCE_PATTERN = re.compile(
    r"!\[(?P<alt>[^\]]*)\]\(attachment:(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)\)"
)


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


def render_terminal_text(text: str) -> str:
    """Replace media references with a plain-text placeholder."""
    return _IMAGE_REFERENCE_PATTERN.sub(
        lambda match: f"[image: {match.group('name')}]",
        text,
    )


def resolve_file_uris(text: str, media_dir: Path) -> str:
    """Rewrite media references to ``file://`` URIs under ``media_dir``."""
    return _IMAGE_REFERENCE_PATTERN.sub(
        lambda match: (
            f"![{match.group('alt')}]"
            + f"({(media_dir / match.group('name')).as_uri()})"
        ),
        text,
    )
