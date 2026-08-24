import argparse

import shtab


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage your exercise library.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    add_parser = subparsers.add_parser(
        "add",
        help="Add a new exercise",
    )

    add_parser.add_argument(
        "prompt",
        type=str,
        nargs="?",
        help="The exercise prompt",
    )

    add_parser.add_argument(
        "answer",
        type=str,
        nargs="?",
        help="The exercise answer",
    )

    add_parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Open markdown editor for prompt and answer",
    )

    add_parser.add_argument(
        "-I",
        "--identifier",
        type=str,
        help="Optional identifier for the exercise",
    )

    browse_parser = subparsers.add_parser(
        "browse",
        help="List all exercises",
    )

    browse_parser.add_argument(
        "-I",
        "--identifier",
        type=str,
        help="Browse exercises under this identifier prefix",
    )

    shtab.add_argument_to(parser)

    return parser
