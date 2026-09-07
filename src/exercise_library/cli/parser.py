import argparse
from collections.abc import Iterable
from pathlib import Path

import shtab

from exercise_library.config import APP_NAME


class Parser:
    def __init__(self) -> None:
        self._parser = argparse.ArgumentParser(
            description="Manage your exercise library.",
        )

        subparsers = self._parser.add_subparsers(dest="command", required=True)

        # ----------------------------------------------------------------------
        # Add command

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
        # edit command
        self._edit_parser = subparsers.add_parser(
            "edit", help="Edit an exercise. Provide identifier or id."
        )

        self._edit_parser.add_argument(
            "-I",
            "--identifier",
            type=str,
        )

        self._edit_parser.add_argument(
            "--id",
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

        shtab.add_argument_to(self._parser)

    def _validate_add_args(
        self,
        args: argparse.Namespace,
    ) -> argparse.Namespace:
        if args.command == "add":
            if not args.interactive and (args.prompt is None or args.answer is None):
                self._add_parser.error(
                    "prompt and answer are required unless --interactive is specified"
                )
            elif args.interactive:
                args.prompt = None
                args.answer = None

        return args

    def _validate_edit_args(self, args: argparse.Namespace) -> argparse.Namespace:
        if args.command == "edit" and (not args.id and not args.identifier):
            self._add_parser.error(
                "at least 'id' or 'identifier' must be provided.",
            )

        return args

    def get_args(
        self,
        args: Iterable[str] | None = None,
        namespace: None = None,
    ) -> argparse.Namespace:
        args = self._parser.parse_args(args, namespace)
        args = self._validate_add_args(args)
        return self._validate_edit_args(args)

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
