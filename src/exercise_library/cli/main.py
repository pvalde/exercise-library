import logging
import sys
from logging.handlers import RotatingFileHandler

from exercise_library.application import ExerciseApplication, ExerciseApplicationError
from exercise_library.cli.exceptions import CLIError
from exercise_library.cli.identifiers_command import list_identifiers
from exercise_library.cli.show_command import show_exercise
from exercise_library.config import APP_NAME
from exercise_library.database import initialize
from exercise_library.locking import ApplicationLockTimeout
from exercise_library.models import ReviewStatus
from exercise_library.paths import log_file_path
from exercise_library.repository import (
    ExerciseRepository,
    MediaRepository,
    ReviewRepository,
)

from .add_command import add_exercise, add_exercise_in_env_editor
from .browse_command import browse_exercises
from .edit_command import edit_exercise, edit_exercise_env_editor
from .media_command import add_media, list_media
from .next_command import next_exercise
from .parser import Parser
from .rate_command import rate_exercise

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    root_logger = logging.getLogger()

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()

    handler = RotatingFileHandler(
        log_file_path(),
        maxBytes=5_000_000,
        backupCount=3,
        encoding="utf-8",
    )

    handler.setLevel(logging.DEBUG)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )

    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(handler)


def main() -> int:

    configure_logging()

    try:
        logger.info("%s started.", APP_NAME)

        parser = Parser()
        args = parser.get_args()

        connection = initialize()
        repository = ExerciseRepository(connection)
        media_repository = MediaRepository(connection)
        review_repository = ReviewRepository(connection)
        application = ExerciseApplication(
            repository, media_repository, review_repository
        )

        if args.command == "add":
            if not args.interactive:
                add_exercise(
                    application,
                    prompt=args.prompt,
                    answer=args.answer,
                    identifier=args.identifier,
                )
            if args.interactive:
                add_exercise_in_env_editor(application)

            print("Exercise was successfully added to the library.")

        elif args.command == "browse":
            browse_exercises(application, args.identifier)

        elif args.command == "backup":
            output = application.backup_data(args.output)
            print(f"Backup file: {output}")

        elif args.command == "edit":
            if args.interactive:
                edit_exercise_env_editor(
                    application=application,
                    exercise_uuid=args.uuid,
                    identifier=args.identifier,
                )

            else:
                edit_exercise(
                    application=application,
                    exercise_uuid=args.uuid,
                    identifier=args.identifier,
                    new_prompt=args.new_prompt,
                    new_answer=args.new_answer,
                    new_identifier=args.new_identifier,
                )

            print("Exercise successfully edited.")

        elif args.command == "show":
            show_exercise(
                application,
                selector=args.selector,
                show_prompt=(args.field != "answer"),
                show_answer=(args.field != "prompt"),
                show_in_webbrowser=args.open_in_browser,
            )

        elif args.command == "next":
            next_exercise(
                application,
                identifier=args.identifier,
                status=ReviewStatus(args.status),
                dry_run=args.dry_run,
            )

        elif args.command == "rate":
            rate_exercise(
                application,
                selector=args.selector,
                rating=args.rating,
            )

        elif args.command == "identifiers":
            list_identifiers(
                application,
                identifier=args.identifier,
                depth=args.depth,
                count=args.count,
            )

        elif args.command == "media":
            if args.media_command == "add":
                add_media(application, args.path)
            elif args.media_command == "list":
                list_media(application)

        logger.info("%s completed successfully.", APP_NAME)
        return 0

    except KeyboardInterrupt:
        logger.info("%s interrupted", APP_NAME)
        print("\nInterrupted.", file=sys.stderr)
        return 130

    except (
        CLIError,
        ExerciseApplicationError,
        ApplicationLockTimeout,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    except Exception:
        logger.exception("Unexpected error")
        print(
            "ERROR: An unexpected error occurred.\n",
            f"See {log_file_path()} ",
            file=sys.stderr,
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())
