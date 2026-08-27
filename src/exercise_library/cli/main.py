import logging
import sys
from logging.handlers import RotatingFileHandler

from exercise_library.application import ExerciseApplication, ExerciseApplicationError
from exercise_library.config import APP_NAME
from exercise_library.database import initialize
from exercise_library.paths import log_file
from exercise_library.repository import ExerciseRepository

from .add_command import AddInteractiveError, add_exercise
from .browse_command import browse_exercises
from .parser import Parser

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    handler = RotatingFileHandler(
        log_file(),
        maxBytes=5_000_000,  # 5 MB
        backupCount=3,
        encoding="utf-8",
    )

    handler.setLevel(logging.DEBUG)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )

    root_logger = logging.getLogger()

    # avoid duplicate log entries if configure_logging() is called again.
    root_logger.handlers.clear()

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

        logger.info("%s completed successfully.", APP_NAME)
        return 0

    except KeyboardInterrupt:
        logger.info("%s interrupted", APP_NAME)
        print("\nInterrupted.", file=sys.stderr)
        return 130

    except (AddInteractiveError, ExerciseApplicationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    except Exception:
        logger.exception("Unexpected error")
        print(
            "ERROR: An unexpected error occurred.\n",
            f"See {log_file()} ",
            file=sys.stderr,
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())
