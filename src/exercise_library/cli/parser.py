import argparse
from pathlib import Path

import shtab

from exercise_library.config import APP_NAME


class Parser:
    def __init__(self) -> None:
        self.parser = argparse.ArgumentParser(
            description="Manage your exercise library.",
        )

        subparsers = self.parser.add_subparsers(dest="command", required=True)

        add_description = (
            "Add a new exercise. Provide prompt and answer, or use --interactive."
        )

        self.add_parser = subparsers.add_parser(
            "add",
            help=add_description,
            description=add_description,
        )

        self.add_parser.add_argument(
            "prompt",
            nargs="?",
            type=str,
            help="The exercise prompt",
        )

        self.add_parser.add_argument(
            "answer",
            nargs="?",
            type=str,
            help="The exercise answer",
        )

        self.add_parser.add_argument(
            "-i",
            "--interactive",
            action="store_true",
            help="Open markdown editor for prompt and answer",
        )

        self.add_parser.add_argument(
            "-I",
            "--identifier",
            type=str,
            help="Optional identifier for the exercise",
        )

        self.browse_parser = subparsers.add_parser(
            "browse",
            help="List all exercises",
        )

        self.browse_parser.add_argument(
            "-I",
            "--identifier",
            type=str,
            help="Browse exercises under this identifier prefix",
        )

        self.backup_parser = subparsers.add_parser(
            "backup",
            help=f"Create a backup of {APP_NAME}'s user data",
        )

        self.backup_parser.add_argument(
            "--output",
            "-o",
            type=self._backup_path,
            help="Path to backup file (must end with '.zip')",
        )

        shtab.add_argument_to(self.parser)

    def _validate_add_args(
        self,
        args: argparse.Namespace,
    ) -> argparse.Namespace:
        if args.command == "add":
            if not args.interactive and (args.prompt is None or args.answer is None):
                self.add_parser.error(
                    "prompt and answer are required unless --interactive is specified"
                )
            elif args.interactive:
                args.prompt = None
                args.answer = None

        return args

    def get_args(
        self,
    ) -> argparse.Namespace:
        args = self.parser.parse_args()
        return self._validate_add_args(args)

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
