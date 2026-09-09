import logging
import sys
from logging.handlers import RotatingFileHandler

from exercise_library.application import ExerciseApplication, ExerciseApplicationError
from exercise_library.cli.exceptions import CLIError
from exercise_library.config import APP_NAME
from exercise_library.database import initialize
from exercise_library.locking import ApplicationLockTimeout
from exercise_library.paths import log_file_path
from exercise_library.repository import ExerciseRepository

from .add_command import add_exercise
from .browse_command import browse_exercises
from .edit_command import edit_exercise, edit_exercise_env_editor
from .parser import Parser

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
        application = ExerciseApplication(repository)

        if args.command == "add":
            add_exercise(application, args)
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
                    exercise_id=args.id,
                    identifier=args.identifier,
                )

            else:
                edit_exercise(
                    application=application,
                    exercise_id=args.id,
                    identifier=args.identifier,
                    new_prompt=args.new_prompt,
                    new_answer=args.new_answer,
                    new_identifier=args.new_identifier,
                )

            print("Exercise successfully edited.")

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
