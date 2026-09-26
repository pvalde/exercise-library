from unittest.mock import Mock

import pytest

from exercise_library.cli.show_command import ShowError, show_exercise


def test_show_exercise_raises_if_not_uuid_and_identifier() -> None:
    application = Mock()

    with pytest.raises(
        ShowError,
        match="At least one of 'uuid' or 'identifier' must be provided.",
    ):
        show_exercise(application, uuid=None, identifier=None)
