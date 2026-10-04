from pathlib import Path

import pytest

from exercise_library.media import (
    hash_file,
    invalid_media_references,
    is_valid_media_name,
    media_type_for_name,
    referenced_media_names,
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
    text = "Look at this: ![diagram](diagram.png)"

    assert render_terminal_text(text) == "Look at this: [image: diagram.png]"


def test_render_terminal_text_replaces_multiple_references() -> None:
    text = "![a](first.png) and ![b](second.jpg)"

    assert render_terminal_text(text) == "[image: first.png] and [image: second.jpg]"


def test_render_terminal_text_leaves_plain_text_untouched() -> None:
    text = "No images here."

    assert render_terminal_text(text) == text


def test_render_terminal_text_ignores_malformed_reference() -> None:
    text = "![bad](has space.png)"

    assert render_terminal_text(text) == text


def test_render_terminal_text_ignores_plain_link() -> None:
    text = "[link](diagram.png)"

    assert render_terminal_text(text) == text


def test_render_terminal_text_ignores_external_url() -> None:
    text = "![remote](https://example.com/diagram.png)"

    assert render_terminal_text(text) == text


def test_render_terminal_text_ignores_relative_path() -> None:
    text = "![local](images/diagram.png)"

    assert render_terminal_text(text) == text


# resolve_file_uris ------------------------------------------------------------


def test_resolve_file_uris_rewrites_to_file_uri(tmp_path: Path) -> None:
    text = "![diagram](diagram.png)"

    result = resolve_file_uris(text, tmp_path)

    assert result == f"![diagram]({(tmp_path / 'diagram.png').as_uri()})"


def test_resolve_file_uris_rewrites_multiple_references(tmp_path: Path) -> None:
    text = "![a](first.png)![b](second.jpg)"

    result = resolve_file_uris(text, tmp_path)

    assert result == (
        f"![a]({(tmp_path / 'first.png').as_uri()})"
        + f"![b]({(tmp_path / 'second.jpg').as_uri()})"
    )


def test_resolve_file_uris_leaves_plain_text_untouched(tmp_path: Path) -> None:
    text = "No images here."

    assert resolve_file_uris(text, tmp_path) == text


def test_resolve_file_uris_preserves_title(tmp_path: Path) -> None:
    text = '![diagram](diagram.png "The diagram")'

    result = resolve_file_uris(text, tmp_path)

    assert result == (
        f'![diagram]({(tmp_path / "diagram.png").as_uri()} "The diagram")'
    )


def test_resolve_file_uris_leaves_external_url_untouched(tmp_path: Path) -> None:
    text = "![remote](https://example.com/diagram.png)"

    assert resolve_file_uris(text, tmp_path) == text


def test_resolve_file_uris_leaves_relative_path_untouched(tmp_path: Path) -> None:
    text = "![local](images/diagram.png)"

    assert resolve_file_uris(text, tmp_path) == text


# referenced_media_names -------------------------------------------------------


def test_referenced_media_names_returns_single_name() -> None:
    assert referenced_media_names("![diagram](diagram.png)") == {"diagram.png"}


def test_referenced_media_names_returns_multiple_names() -> None:
    text = "![a](first.png) and ![b](second.jpg)"

    assert referenced_media_names(text) == {"first.png", "second.jpg"}


def test_referenced_media_names_deduplicates_names() -> None:
    text = "![a](diagram.png) ![b](diagram.png)"

    assert referenced_media_names(text) == {"diagram.png"}


def test_referenced_media_names_returns_empty_for_plain_text() -> None:
    assert referenced_media_names("No images here.") == set()


def test_referenced_media_names_ignores_malformed_reference() -> None:
    assert referenced_media_names("![bad](has space.png)") == set()


def test_referenced_media_names_ignores_external_url() -> None:
    assert referenced_media_names("![remote](https://example.com/a.png)") == set()


def test_referenced_media_names_ignores_relative_path() -> None:
    assert referenced_media_names("![local](images/diagram.png)") == set()


def test_referenced_media_names_reads_name_with_title() -> None:
    text = '![diagram](diagram.png "The diagram")'

    assert referenced_media_names(text) == {"diagram.png"}


# invalid_media_references ----------------------------------------------------


def test_invalid_media_references_detects_misspelled_scheme() -> None:
    text = "![an image](attatchment:missing.png)"

    assert invalid_media_references(text) == ["attatchment:missing.png"]


def test_invalid_media_references_detects_invalid_name() -> None:
    text = "![an image](.hidden.png)"

    assert invalid_media_references(text) == [".hidden.png"]


def test_invalid_media_references_returns_empty_for_valid_name() -> None:
    assert invalid_media_references("![ok](diagram.png)") == []


def test_invalid_media_references_detects_external_url() -> None:
    text = "![remote](https://example.com/diagram.png)"

    assert invalid_media_references(text) == ["https://example.com/diagram.png"]


def test_invalid_media_references_detects_relative_path() -> None:
    text = "![local](images/diagram.png)"

    assert invalid_media_references(text) == ["images/diagram.png"]


def test_invalid_media_references_detects_non_media_extension() -> None:
    text = "![doc](file.txt)"

    assert invalid_media_references(text) == ["file.txt"]


def test_invalid_media_references_returns_sorted_destinations() -> None:
    text = "![b](https://example.com/b.png)![a](images/a.png)"

    assert invalid_media_references(text) == [
        "https://example.com/b.png",
        "images/a.png",
    ]


def test_invalid_media_references_reads_destination_with_title() -> None:
    text = '![remote](https://example.com/a.png "remote")'

    assert invalid_media_references(text) == ["https://example.com/a.png"]
