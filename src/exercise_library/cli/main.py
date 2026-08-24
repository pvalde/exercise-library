from exercise_library.application import ExerciseApplication
from exercise_library.database import initialize
from exercise_library.repository import ExerciseRepository

from .add_command import add_exercise
from .browse_command import browse_exercises
from .parser import create_parser


def main() -> None:
    parser = create_parser()
    args = parser.parse_args()

    connection = initialize()
    repository = ExerciseRepository(connection)
    application = ExerciseApplication(repository)

    if args.command == "add":
        add_exercise(application, args)
    elif args.command == "browse":
        browse_exercises(application, args.identifier)
