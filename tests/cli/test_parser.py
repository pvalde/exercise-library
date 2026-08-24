import pytest

from exercise_library.cli.parser import create_parser


def test_create_parser_requires_command() -> None:
    parser = create_parser()

    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_create_parser_parses_add_arguments() -> None:
    parser = create_parser()

    args = parser.parse_args(["add", "prompt", "answer"])

    assert args.command == "add"
    assert args.prompt == "prompt"
    assert args.answer == "answer"
    assert args.interactive is False


def test_create_parser_parses_identifier() -> None:
    parser = create_parser()

    args = parser.parse_args(
        [
            "add",
            "-I",
            "book::chapter01::exercise05",
            "prompt",
            "answer",
        ]
    )

    assert args.command == "add"
    assert args.identifier == "book::chapter01::exercise05"
    assert args.prompt == "prompt"
    assert args.answer == "answer"
    assert args.interactive is False


def test_create_parser_identifier_is_optional() -> None:
    parser = create_parser()

    args = parser.parse_args(["add", "prompt", "answer"])

    assert args.identifier is None


def test_create_parser_parses_interactive_flag() -> None:
    parser = create_parser()

    args = parser.parse_args(["add", "-i"])

    assert args.command == "add"
    assert args.prompt is None
    assert args.answer is None
    assert args.interactive is True


def test_create_parser_accepts_long_interactive_flag() -> None:
    parser = create_parser()

    args = parser.parse_args(["add", "--interactive"])

    assert args.interactive is True


def test_create_parser_parses_browse_command() -> None:
    parser = create_parser()

    args = parser.parse_args(["browse"])

    assert args.command == "browse"
    assert args.identifier is None


def test_create_parser_parses_browse_identifier() -> None:
    parser = create_parser()

    args = parser.parse_args(
        [
            "browse",
            "-I",
            "book::chapter01",
        ]
    )

    assert args.command == "browse"
    assert args.identifier == "book::chapter01"


def test_create_parser_accepts_long_browse_identifier_flag() -> None:
    parser = create_parser()

    args = parser.parse_args(
        [
            "browse",
            "--identifier",
            "book::chapter01",
        ]
    )

    assert args.command == "browse"
    assert args.identifier == "book::chapter01"


def test_create_parser_rejects_short_browse_identifier_flag() -> None:
    parser = create_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "browse",
                "-i",
                "book::chapter01",
            ]
        )
