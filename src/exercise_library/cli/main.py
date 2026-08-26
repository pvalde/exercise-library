from exercise_library.application import ExerciseApplication
from exercise_library.database import initialize
from exercise_library.repository import ExerciseRepository

from .add_command import add_exercise
from .browse_command import browse_exercises
from .parser import create_parser


def main() -> None:
    parser, subparsers = create_parser()
    args = parser.parse_args()

    connection = initialize()
    repository = ExerciseRepository(connection)
    application = ExerciseApplication(repository)

    if args.command == "add":
        result = add_exercise(application, args)
        if result is False:
            if args.interactive:
                print("ERROR: Prompt and answer cannot be empty.")
            else:
                print(
                    "ERROR: Prompt and answer are required unless",
                    " --interactive is used.",
                )

            print(" " * 7 + "Could not add exercise to the library.")
            print()
            subparsers["add"].print_help()

        else:
            print("Exercise was successfully added to the library.")

    elif args.command == "browse":
        browse_exercises(application, args.identifier)
