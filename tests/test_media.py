from pathlib import Path

import pytest

from exercise_library.media import (
    hash_file,
    is_valid_media_name,
    media_type_for_name,
)


@pytest.mark.parametrize(
    "name",
    [
        "diagram.png",
        "figure-1.jpg",
        "figure_1.jpeg",
        "a.b.c.gif",
        "A1.webp",
        "photo2024-01-02.svg",
    ],
)
def test_is_valid_media_name_accepts(name: str) -> None:
    assert is_valid_media_name(name)


@pytest.mark.parametrize(
    "name",
    [
        "",
        " leading.png",
        "trailing .png",
        ".hidden.png",
        "-leading-dash.png",
        "_leading-underscore.png",
        "with space.png",
        "path/name.png",
        "back\\slash.png",
        "semi;colon.png",
    ],
)
def test_is_valid_media_name_rejects(name: str) -> None:
    assert not is_valid_media_name(name)


@pytest.mark.parametrize(
    ("name", "media_type"),
    [
        ("diagram.png", "image/png"),
        ("diagram.PNG", "image/png"),
        ("figure.jpg", "image/jpeg"),
        ("figure.JPEG", "image/jpeg"),
        ("animation.gif", "image/gif"),
        ("photo.webp", "image/webp"),
        ("vector.svg", "image/svg+xml"),
    ],
)
def test_media_type_for_name_returns_type(name: str, media_type: str) -> None:
    assert media_type_for_name(name) == media_type


@pytest.mark.parametrize(
    "name",
    [
        "document.pdf",
        "notes.txt",
        "archive.zip",
        "no-extension",
        "trailing.",
    ],
)
def test_media_type_for_name_returns_none_when_unsupported(name: str) -> None:
    assert media_type_for_name(name) is None


def test_hash_file_matches_known_digest(tmp_path: Path) -> None:
    path = tmp_path / "file.bin"
    path.write_bytes(b"hello")

    assert (
        hash_file(path)
        == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    )


def test_hash_file_is_content_based(tmp_path: Path) -> None:
    first = tmp_path / "first.bin"
    second = tmp_path / "second.bin"

    first.write_bytes(b"same content")
    second.write_bytes(b"same content")

    assert hash_file(first) == hash_file(second)


def test_hash_file_differs_for_different_content(tmp_path: Path) -> None:
    first = tmp_path / "first.bin"
    second = tmp_path / "second.bin"

    first.write_bytes(b"content a")
    second.write_bytes(b"content b")

    assert hash_file(first) != hash_file(second)
