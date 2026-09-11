from unittest.mock import Mock

import pytest

from exercise_library.cli.show_command import ShowError, show_exercise


def test_show_exercise_raises_if_not_id_and_identifier() -> None:
    application = Mock()

    with pytest.raises(
        ShowError,
        match="At least one of 'id' or 'identifier' must be provided.",
    ):
        show_exercise(application, id=None, identifier=None)
