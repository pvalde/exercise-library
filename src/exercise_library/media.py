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

_IMAGE_PATTERN = re.compile(
    r"!\[(?P<alt>[^\]]*)\]\(\s*(?P<destination>[^)\s]+)"
    r"(?:\s+(?P<title>\"[^\"]*\"|'[^']*'))?\s*\)"
)


def is_valid_media_name(name: str) -> bool:
    """Return whether ``name`` is a safe, referenceable media file name."""
    return bool(_MEDIA_NAME_PATTERN.fullmatch(name))


def media_type_for_name(name: str) -> str | None:
    """Return the media type for a supported extension, or None."""
    return _MEDIA_TYPES_BY_EXTENSION.get(Path(name).suffix.lower())


def is_media_reference(destination: str) -> bool:
    """Return whether an image destination refers to stored media.

    A destination is a media reference when it is a bare file name (no scheme
    and no path separator) with a supported media extension.
    """
    if "://" in destination or "/" in destination:
        return False

    return (
        is_valid_media_name(destination)
        and media_type_for_name(destination) is not None
    )


def referenced_media_names(text: str) -> set[str]:
    """Return the media names referenced by markdown images in ``text``."""
    return {
        match.group("destination")
        for match in _IMAGE_PATTERN.finditer(text)
        if is_media_reference(match.group("destination"))
    }


def invalid_media_references(text: str) -> list[str]:
    """Return image destinations that do not refer to stored media."""
    return sorted(
        {
            match.group("destination")
            for match in _IMAGE_PATTERN.finditer(text)
            if not is_media_reference(match.group("destination"))
        }
    )


def hash_file(path: Path) -> str:
    """Return the hex-encoded SHA-256 digest of the file at ``path``."""
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def render_terminal_text(text: str) -> str:
    """Replace media references with a plain-text placeholder."""
    return _IMAGE_PATTERN.sub(_render_terminal_match, text)


def _render_terminal_match(match: re.Match[str]) -> str:
    destination = match.group("destination")

    if not is_media_reference(destination):
        return match.group(0)

    return f"[image: {destination}]"


def resolve_file_uris(text: str, media_dir: Path) -> str:
    """Rewrite media references to ``file://`` URIs under ``media_dir``."""
    return _IMAGE_PATTERN.sub(lambda match: _resolve_match(match, media_dir), text)


def _resolve_match(match: re.Match[str], media_dir: Path) -> str:
    destination = match.group("destination")

    if not is_media_reference(destination):
        return match.group(0)

    title = match.group("title")
    title_part = f" {title}" if title else ""

    return f"![{match.group('alt')}]({(media_dir / destination).as_uri()}{title_part})"
