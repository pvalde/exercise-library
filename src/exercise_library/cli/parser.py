import argparse
from collections.abc import Iterable
from pathlib import Path
from typing import Any
from uuid import UUID

import shtab

from exercise_library.config import APP_NAME


class _OnceAction(argparse.Action):
    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: Any,
        option_string: str | None = None,
    ) -> None:
        if getattr(namespace, self.dest, None) is not None:
            parser.error(f"{option_string} may only be specified once")

        setattr(namespace, self.dest, values)


class Parser:
    def __init__(self) -> None:
        self._parser = argparse.ArgumentParser(
            description="Manage your exercise library.",
        )

        subparsers = self._parser.add_subparsers(dest="command", required=True)

        # ----------------------------------------------------------------------
        # Add command
        # ----------------------------------------------------------------------
        add_description = (
            "Add a new exercise. Provide prompt and answer, or use --interactive."
        )

        self._add_parser = subparsers.add_parser(
            "add",
            help=add_description,
            description=add_description,
        )

        self._add_parser.add_argument(
            "prompt",
            nargs="?",
            type=str,
            help="The exercise prompt",
        )

        self._add_parser.add_argument(
            "answer",
            nargs="?",
            type=str,
            help="The exercise answer",
        )

        self._add_parser.add_argument(
            "-i",
            "--interactive",
            action="store_true",
            help="Open markdown editor for prompt and answer",
        )

        self._add_parser.add_argument(
            "-I",
            "--identifier",
            type=str,
            help="Optional identifier for the exercise",
        )

        # ----------------------------------------------------------------------
        # Browse command
        # ----------------------------------------------------------------------
        self._browse_parser = subparsers.add_parser(
            "browse",
            help="List all exercises",
        )

        self._browse_parser.add_argument(
            "-I",
            "--identifier",
            type=str,
            help="Browse exercises under this identifier prefix",
        )

        # ----------------------------------------------------------------------
        # Backup command
        # ----------------------------------------------------------------------
        self._backup_parser = subparsers.add_parser(
            "backup",
            help=f"Create a backup of {APP_NAME}'s user data",
        )

        self._backup_parser.add_argument(
            "--output",
            "-o",
            type=self._backup_path,
            help="Path to backup file (must end with '.zip')",
        )

        # ----------------------------------------------------------------------
        # Edit command
        # ----------------------------------------------------------------------
        self._edit_parser = subparsers.add_parser(
            "edit", help="Edit an exercise. Provide identifier or uuid."
        )

        self._edit_parser.add_argument(
            "-I",
            "--identifier",
            type=str,
        )

        self._edit_parser.add_argument(
            "--uuid",
            type=str,
        )

        self._edit_parser.add_argument(
            "--new-prompt",
            type=str,
        )

        self._edit_parser.add_argument(
            "--new-answer",
            type=str,
        )

        self._edit_parser.add_argument(
            "--new-identifier",
            type=str,
        )

        self._edit_parser.add_argument(
            "--interactive",
            "-i",
            action="store_true",
            help="Open markdown editor for prompt and answer",
        )

        # ----------------------------------------------------------------------
        # Show command
        # ----------------------------------------------------------------------
        self._show_parser = subparsers.add_parser(
            "show",
            help="Show an exercise.",
        )

        self._show_parser.add_argument(
            "selector",
            type=str,
            help="Exercise identifier or uuid",
        )

        self._show_parser.add_argument(
            "--field",
            "-f",
            choices=["prompt", "answer"],
            action=_OnceAction,
            help="Show only the specified field.",
        )

        self._show_parser.add_argument(
            "--open-in-browser",
            "-o",
            action="store_true",
            help="Open exercise in default web browser.",
        )

        # ----------------------------------------------------------------------
        # Identifiers command
        # ----------------------------------------------------------------------
        self._identifiers_parser = subparsers.add_parser(
            "identifiers",
            help="List identifier prefixes",
        )

        self._identifiers_parser.add_argument(
            "-I",
            "--identifier",
            type=str,
            default=None,
            help="List prefixes under this identifier",
        )

        self._identifiers_parser.add_argument(
            "-d",
            "--depth",
            type=self._positive_int,
            default=None,
            help="Maximum number of identifier segments",
        )

        self._identifiers_parser.add_argument(
            "-c",
            "--count",
            action="store_true",
            help="Show exercise counts for each prefix identifier.",
        )

        # ----------------------------------------------------------------------
        # Media command
        # ----------------------------------------------------------------------
        self._media_parser = subparsers.add_parser(
            "media",
            help="Manage media files",
        )

        media_subparsers = self._media_parser.add_subparsers(
            dest="media_command",
            required=True,
        )

        self._media_add_parser = media_subparsers.add_parser(
            "add",
            help="Add a media file",
        )

        self._media_add_parser.add_argument(
            "path",
            type=self._existing_file,
            help="Path to the media file to add",
        )

        media_subparsers.add_parser(
            "list",
            help="List stored media",
        )

        # ------------------------------------------------------------------
        # Next command
        # ------------------------------------------------------------------
        self._next_parser = subparsers.add_parser(
            "next",
            help="Print the next exercise to study (identifier or uuid)",
        )

        self._next_parser.add_argument(
            "-I",
            "--identifier",
            type=str,
            default=None,
            help="Only consider exercises under this identifier prefix",
        )

        self._next_parser.add_argument(
            "--status",
            choices=["all", "new", "reviewed"],
            default="all",
            help="Filter by review status (default: all)",
        )

        self._next_parser.add_argument(
            "--dry-run",
            action="store_true",
            help="List the top candidates with their weights instead of picking one",
        )

        # ------------------------------------------------------------------
        # Rate command
        # ------------------------------------------------------------------
        self._rate_parser = subparsers.add_parser(
            "rate",
            help="Record a review rating for an exercise",
        )

        self._rate_parser.add_argument(
            "rating",
            choices=["wrong", "hard", "good", "easy"],
            help="How the review went",
        )

        rate_selector = self._rate_parser.add_mutually_exclusive_group(required=True)

        rate_selector.add_argument(
            "-I",
            "--identifier",
            type=str,
        )

        rate_selector.add_argument(
            "--uuid",
            type=UUID,
        )

        shtab.add_argument_to(self._parser)

    def _validate_add_args(
        self,
        args: argparse.Namespace,
    ) -> argparse.Namespace:
        if not args.interactive and (args.prompt is None or args.answer is None):
            self._add_parser.error(
                "prompt and answer are required unless --interactive is specified"
            )
        if args.interactive:
            args.prompt = None
            args.answer = None
            args.identifier = None

        return args

    def _validate_edit_args(self, args: argparse.Namespace) -> argparse.Namespace:
        if not args.interactive:
            if not args.uuid and not args.identifier:
                self._edit_parser.error(
                    "at least 'uuid' or 'identifier' must be provided.",
                )
            if (
                args.new_prompt is None
                and args.new_answer is None
                and args.new_identifier is None
            ):
                self._edit_parser.error(
                    "Please provide at least one of: "
                    + "'new prompt', 'new answer', or 'new identifier'."
                )
        if args.interactive:
            args.new_prompt = None
            args.new_answer = None
            args.new_identifier = None

        return args

    def get_args(
        self,
        args: Iterable[str] | None = None,
        namespace: None = None,
    ) -> argparse.Namespace:
        args = self._parser.parse_args(args, namespace)
        if args.command == "add":
            args = self._validate_add_args(args)
        elif args.command == "edit":
            args = self._validate_edit_args(args)

        return args

    def _backup_path(self, value: str) -> Path:
        path = Path(value).expanduser()
        filename = path.name
        suffix = ".zip"

        if not filename.lower().endswith(suffix):
            raise argparse.ArgumentTypeError("backup path must end with '.zip'")

        filename_without_suffix = filename[: -len(suffix)]

        if not filename_without_suffix.strip():
            raise argparse.ArgumentTypeError("backup filename must not be empty")

        if not path.parent.exists():
            raise argparse.ArgumentTypeError(
                f"parent directory does not exist: {path.parent}"
            )

        if not path.parent.is_dir():
            raise argparse.ArgumentTypeError(
                f"parent path is not a directory: {path.parent}"
            )

        return path

    def _positive_int(self, value: str) -> int:
        number = int(value)
        if number < 1:
            raise argparse.ArgumentTypeError("must be a positive integer")
        return number

    def _existing_file(self, value: str) -> Path:
        path = Path(value).expanduser()

        if not path.exists():
            raise argparse.ArgumentTypeError(f"file does not exist: {path}")

        if not path.is_file():
            raise argparse.ArgumentTypeError(f"not a file: {path}")

        return path
