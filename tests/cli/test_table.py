import pytest

from exercise_library.cli.table import print_three_column_table


def test_prints_headers_and_separator(
    capsys: pytest.CaptureFixture[str],
) -> None:
    print_three_column_table(
        first_col_width=4,
        second_col_max=10,
        headers=["ID", "NAME", "VALUE"],
        rows=[["1", "a", "x"]],
        terminal_width=40,
    )

    out = capsys.readouterr().out.splitlines()
    assert out[0].startswith("ID")
    assert set(out[1]) == {"-"}
    assert len(out[1]) == len(out[0])


def test_row_cells_in_order(capsys: pytest.CaptureFixture[str]) -> None:
    print_three_column_table(
        first_col_width=4,
        second_col_max=10,
        headers=["ID", "NAME", "VALUE"],
        rows=[["1", "alpha", "hello"]],
        terminal_width=40,
    )

    row = capsys.readouterr().out.splitlines()[2]
    assert row.startswith("1")
    assert "alpha" in row
    assert row.endswith("hello")


def test_third_column_truncated_with_ellipsis_when_narrow(
    capsys: pytest.CaptureFixture[str],
) -> None:
    print_three_column_table(
        first_col_width=4,
        second_col_max=10,
        headers=["ID", "NAME", "VALUE"],
        rows=[["1", "a", "a-very-long-value-that-does-not-fit"]],
        terminal_width=20,
    )

    row = capsys.readouterr().out.splitlines()[2]
    assert row.endswith("...")
    assert "does-not-fit" not in row


def test_third_column_not_truncated_when_wide(
    capsys: pytest.CaptureFixture[str],
) -> None:
    print_three_column_table(
        first_col_width=4,
        second_col_max=10,
        headers=["ID", "NAME", "VALUE"],
        rows=[["1", "a", "short"]],
        terminal_width=120,
    )

    row = capsys.readouterr().out.splitlines()[2]
    assert row.endswith("short")
    assert "..." not in row


def test_second_column_adapts_to_longest_value(
    capsys: pytest.CaptureFixture[str],
) -> None:
    print_three_column_table(
        first_col_width=4,
        second_col_max=40,
        headers=["ID", "NAME", "VALUE"],
        rows=[["1", "a", "x"], ["2", "bbbb", "y"]],
        terminal_width=60,
    )

    lines = capsys.readouterr().out.splitlines()
    # VALUE column starts right after the longest second-column value ("bbbb")
    # padded to the same width, so its index aligns across all rows.
    x_idx = lines[2].index("x")
    y_idx = lines[3].index("y")
    assert x_idx == y_idx


def test_third_column_has_minimum_width() -> None:
    # tiny terminal width must not produce a negative/tiny third column;
    # the row should still render (third column floored at 20)
    import io
    from contextlib import redirect_stdout

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        print_three_column_table(
            first_col_width=4,
            second_col_max=10,
            headers=["ID", "NAME", "VALUE"],
            rows=[["1", "a", "x"]],
            terminal_width=10,
        )

    lines = buffer.getvalue().splitlines()
    assert len(lines) == 3
    assert lines[2].endswith("x")


def test_third_column_minimum_width_survives_zero_terminal_width() -> None:
    import io
    from contextlib import redirect_stdout

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        print_three_column_table(
            first_col_width=4,
            second_col_max=10,
            headers=["ID", "NAME", "VALUE"],
            rows=[["1", "a", "x"]],
            terminal_width=0,
        )

    lines = buffer.getvalue().splitlines()
    assert len(lines) == 3
    assert lines[2].endswith("x")
