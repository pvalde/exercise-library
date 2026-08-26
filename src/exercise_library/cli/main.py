from sqlite3 import Connection
import sys

from exercise_library.application import ExerciseApplication, ExerciseApplicationError
from exercise_library.database import initialize
from exercise_library.repository import ExerciseRepository

from .add_command import AddInteractiveError, add_exercise
from .browse_command import browse_exercises
from .parser import Parser


def main() -> int:
    parser = Parser()
    args = parser.get_args()

    try:
        connection = initialize()
        repository = ExerciseRepository(connection)
        application = ExerciseApplication(repository)

        if args.command == "add":
            add_exercise(application, args)
            print("Exercise was successfully added to the library.")

        elif args.command == "browse":
            browse_exercises(application, args.identifier)

        return 0

    except AddInteractiveError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    except ExerciseApplicationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    except Exception:
        print("ERROR: An unexpected error occurred. ", file=sys.stderr)

        return 1


if __name__ == "__main__":
    raise SystemExit(main())
