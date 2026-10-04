from pathlib import Path

import pytest

from exercise_library.media import (
    hash_file,
    is_valid_media_name,
    media_type_for_name,
    render_terminal_text,
    resolve_file_uris,
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


# render_terminal_text ---------------------------------------------------------


def test_render_terminal_text_replaces_reference_with_placeholder() -> None:
    text = "Look at this: ![diagram](attachment:diagram.png)"

    assert render_terminal_text(text) == "Look at this: [image: diagram.png]"


def test_render_terminal_text_replaces_multiple_references() -> None:
    text = "![a](attachment:first.png) and ![b](attachment:second.jpg)"

    assert render_terminal_text(text) == "[image: first.png] and [image: second.jpg]"


def test_render_terminal_text_leaves_plain_text_untouched() -> None:
    text = "No images here."

    assert render_terminal_text(text) == text


def test_render_terminal_text_ignores_malformed_reference() -> None:
    text = "![bad](attachment:has space.png)"

    assert render_terminal_text(text) == text


def test_render_terminal_text_ignores_plain_link() -> None:
    text = "[link](attachment:diagram.png)"

    assert render_terminal_text(text) == text


# resolve_file_uris ------------------------------------------------------------


def test_resolve_file_uris_rewrites_to_file_uri(tmp_path: Path) -> None:
    text = "![diagram](attachment:diagram.png)"

    result = resolve_file_uris(text, tmp_path)

    assert result == f"![diagram]({(tmp_path / 'diagram.png').as_uri()})"


def test_resolve_file_uris_rewrites_multiple_references(tmp_path: Path) -> None:
    text = "![a](attachment:first.png)![b](attachment:second.jpg)"

    result = resolve_file_uris(text, tmp_path)

    assert result == (
        f"![a]({(tmp_path / 'first.png').as_uri()})"
        + f"![b]({(tmp_path / 'second.jpg').as_uri()})"
    )


def test_resolve_file_uris_leaves_plain_text_untouched(tmp_path: Path) -> None:
    text = "No images here."

    assert resolve_file_uris(text, tmp_path) == text
