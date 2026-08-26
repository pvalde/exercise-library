import argparse
from unittest.mock import Mock

import pytest

import exercise_library.cli.main as cli


def test_main_adds_exercise(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parser = Mock()
    subparsers = Mock()

    parser.parse_args.return_value = argparse.Namespace(
        command="add",
        prompt="prompt",
        answer="answer",
        interactive=False,
        identifier=None,
    )

    initialize_mock = Mock(return_value="connection")
    repository_mock = Mock()
    application_mock = Mock()
    add_exercise_mock = Mock()

    monkeypatch.setattr(
        cli,
        "create_parser",
        Mock(return_value=(parser, subparsers)),
    )
    monkeypatch.setattr(
        cli,
        "initialize",
        initialize_mock,
    )
    monkeypatch.setattr(
        cli,
        "ExerciseRepository",
        Mock(return_value=repository_mock),
    )
    monkeypatch.setattr(
        cli,
        "ExerciseApplication",
        Mock(return_value=application_mock),
    )
    monkeypatch.setattr(
        cli,
        "add_exercise",
        add_exercise_mock,
    )

    cli.main()

    initialize_mock.assert_called_once()
    add_exercise_mock.assert_called_once_with(
        application_mock,
        parser.parse_args.return_value,
    )


def test_main_browse_exercises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parser = Mock()
    subparsers = Mock()

    parser.parse_args.return_value = argparse.Namespace(
        command="browse",
        identifier=None,
    )

    initialize_mock = Mock(return_value="connection")
    repository_mock = Mock()
    application_mock = Mock()
    browse_exercises_mock = Mock()

    monkeypatch.setattr(
        cli,
        "create_parser",
        Mock(return_value=(parser, subparsers)),
    )
    monkeypatch.setattr(
        cli,
        "initialize",
        initialize_mock,
    )
    monkeypatch.setattr(
        cli,
        "ExerciseRepository",
        Mock(return_value=repository_mock),
    )
    monkeypatch.setattr(
        cli,
        "ExerciseApplication",
        Mock(return_value=application_mock),
    )
    monkeypatch.setattr(
        cli,
        "browse_exercises",
        browse_exercises_mock,
    )

    cli.main()

    initialize_mock.assert_called_once()
    browse_exercises_mock.assert_called_once_with(
        application_mock,
        None,
    )


def test_main_browses_exercises_with_identifier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parser = Mock()
    subparsers = Mock()

    parser.parse_args.return_value = argparse.Namespace(
        command="browse",
        identifier="book::chapter01",
    )

    initialize_mock = Mock(return_value="connection")
    repository_mock = Mock()
    application_mock = Mock()
    browse_exercises_mock = Mock()

    monkeypatch.setattr(
        cli,
        "create_parser",
        Mock(return_value=(parser, subparsers)),
    )
    monkeypatch.setattr(
        cli,
        "initialize",
        initialize_mock,
    )
    monkeypatch.setattr(
        cli,
        "ExerciseRepository",
        Mock(return_value=repository_mock),
    )
    monkeypatch.setattr(
        cli,
        "ExerciseApplication",
        Mock(return_value=application_mock),
    )
    monkeypatch.setattr(
        cli,
        "browse_exercises",
        browse_exercises_mock,
    )

    cli.main()

    initialize_mock.assert_called_once()
    browse_exercises_mock.assert_called_once_with(
        application_mock,
        "book::chapter01",
    )
