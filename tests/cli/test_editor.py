import os
import subprocess
from typing import Never
from unittest.mock import Mock

import pytest

from exercise_library.cli.editor import edit_in_editor


def test_edit_in_editor_uses_visual_over_editor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VISUAL", "visual-editor")
    monkeypatch.setenv("EDITOR", "other-editor")

    fake_run = Mock()
    monkeypatch.setattr(
        "exercise_library.cli.editor.subprocess.run",
        fake_run,
    )

    edit_in_editor("prompt")

    command = fake_run.call_args.args[0]

    assert command[0] == "visual-editor"


def test_edit_in_editor_falls_back_to_editor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("VISUAL", raising=False)
    monkeypatch.setenv("EDITOR", "my-editor")

    fake_run = Mock()
    monkeypatch.setattr(
        "exercise_library.cli.editor.subprocess.run",
        fake_run,
    )

    edit_in_editor("answer")

    command = fake_run.call_args.args[0]

    assert command[0] == "my-editor"


def test_edit_in_editor_supports_editor_arguments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("VISUAL", raising=False)
    monkeypatch.setenv("EDITOR", "my-editor --wait --foo")

    fake_run = Mock()
    monkeypatch.setattr(
        "exercise_library.cli.editor.subprocess.run",
        fake_run,
    )

    edit_in_editor("prompt")

    command = fake_run.call_args.args[0]

    assert command[:-1] == [
        "my-editor",
        "--wait",
        "--foo",
    ]


def test_edit_in_editor_exits_when_no_editor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("VISUAL", raising=False)
    monkeypatch.delenv("EDITOR", raising=False)

    with pytest.raises(SystemExit) as exc_info:
        edit_in_editor("prompt")

    assert exc_info.value.code == 1


def test_edit_in_editor_removes_generated_comments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EDITOR", "editor")

    def fake_editor(command: list[str], check: bool) -> None:
        filename = command[-1]

        with open(filename, "a", encoding="utf-8") as f:
            f.write("# My exercise\n\n")
            f.write("This is **Markdown**.\n")

    fake_run = Mock(side_effect=fake_editor)
    monkeypatch.setattr(
        "exercise_library.cli.editor.subprocess.run",
        fake_run,
    )

    result = edit_in_editor("prompt")

    assert result == "# My exercise\n\nThis is **Markdown**."


def test_edit_in_editor_preserves_other_html_comments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EDITOR", "editor")

    def fake_editor(command: list[str], check: bool) -> None:
        filename = command[-1]

        with open(filename, "a", encoding="utf-8") as f:
            f.write("<!-- Keep this comment -->\n")
            f.write("Some content\n")

    fake_run = Mock(side_effect=fake_editor)
    monkeypatch.setattr(
        "exercise_library.cli.editor.subprocess.run",
        fake_run,
    )

    result = edit_in_editor("prompt")

    assert result == "<!-- Keep this comment -->\nSome content"


def test_edit_in_editor_strips_surrounding_whitespace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EDITOR", "editor")

    def fake_editor(command: list[str], check: bool) -> None:
        filename = command[-1]

        with open(filename, "a", encoding="utf-8") as f:
            f.write("\n\n  Some content  \n\n")

    fake_run = Mock(side_effect=fake_editor)
    monkeypatch.setattr(
        "exercise_library.cli.editor.subprocess.run",
        fake_run,
    )

    result = edit_in_editor("prompt")

    assert result == "Some content"


def test_edit_in_editor_returns_empty_on_editor_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EDITOR", "editor")

    def fake_editor(command: list[str], check: bool) -> Never:
        raise subprocess.CalledProcessError(1, command)

    fake_run = Mock(side_effect=fake_editor)
    monkeypatch.setattr(
        "exercise_library.cli.editor.subprocess.run",
        fake_run,
    )

    result = edit_in_editor("prompt")

    assert result == ""


def test_edit_in_editor_deletes_temporary_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EDITOR", "editor")

    def fake_editor(command: list[str], check: bool) -> None:
        filename = command[-1]

        with open(filename, "a", encoding="utf-8") as f:
            f.write("content\n")

    fake_run = Mock(side_effect=fake_editor)
    monkeypatch.setattr(
        "exercise_library.cli.editor.subprocess.run",
        fake_run,
    )

    edit_in_editor("prompt")

    filename = fake_run.call_args.args[0][-1]

    assert not os.path.exists(filename)


def test_edit_in_editor_deletes_file_when_editor_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EDITOR", "editor")

    def fake_editor(command: list[str], check: bool) -> Never:
        raise subprocess.CalledProcessError(1, command)

    fake_run = Mock(side_effect=fake_editor)
    monkeypatch.setattr(
        "exercise_library.cli.editor.subprocess.run",
        fake_run,
    )

    result = edit_in_editor("prompt")

    assert result == ""

    filename = fake_run.call_args.args[0][-1]

    assert not os.path.exists(filename)
