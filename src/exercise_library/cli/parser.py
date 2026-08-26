import argparse

import shtab


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
