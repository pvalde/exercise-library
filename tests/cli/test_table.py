import pytest

from exercise_library.cli.table import Adapt, Fill, Fixed, print_table


def test_prints_headers_and_separator(
    capsys: pytest.CaptureFixture[str],
) -> None:
    print_table(
        headers=["ID", "NAME", "VALUE"],
        rows=[["1", "a", "x"]],
        widths=[Fixed(4), Adapt(10), Fill()],
        terminal_width=40,
    )

    out = capsys.readouterr().out.splitlines()
    assert out[0].startswith("ID")
    assert set(out[1]) == {"-"}
    assert len(out[1]) == len(out[0])


def test_row_cells_in_order(capsys: pytest.CaptureFixture[str]) -> None:
    print_table(
        headers=["ID", "NAME", "VALUE"],
        rows=[["1", "alpha", "hello"]],
        widths=[Fixed(4), Adapt(10), Fill()],
        terminal_width=40,
    )

    row = capsys.readouterr().out.splitlines()[2]
    assert row.startswith("1")
    assert "alpha" in row
    assert row.endswith("hello")


def test_third_column_truncated_with_ellipsis_when_narrow(
    capsys: pytest.CaptureFixture[str],
) -> None:
    print_table(
        headers=["ID", "NAME", "VALUE"],
        rows=[["1", "a", "a-very-long-value-that-does-not-fit"]],
        widths=[Fixed(4), Adapt(10), Fill()],
        terminal_width=20,
    )

    row = capsys.readouterr().out.splitlines()[2]
    assert row.endswith("...")
    assert "does-not-fit" not in row


def test_third_column_not_truncated_when_wide(
    capsys: pytest.CaptureFixture[str],
) -> None:
    print_table(
        headers=["ID", "NAME", "VALUE"],
        rows=[["1", "a", "short"]],
        widths=[Fixed(4), Adapt(10), Fill()],
        terminal_width=120,
    )

    row = capsys.readouterr().out.splitlines()[2]
    assert row.endswith("short")
    assert "..." not in row


def test_second_column_adapts_to_longest_value(
    capsys: pytest.CaptureFixture[str],
) -> None:
    print_table(
        headers=["ID", "NAME", "VALUE"],
        rows=[["1", "a", "x"], ["2", "bbbb", "y"]],
        widths=[Fixed(4), Adapt(40), Fill()],
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
        print_table(
            headers=["ID", "NAME", "VALUE"],
            rows=[["1", "a", "x"]],
            widths=[Fixed(4), Adapt(10), Fill()],
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
        print_table(
            headers=["ID", "NAME", "VALUE"],
            rows=[["1", "a", "x"]],
            widths=[Fixed(4), Adapt(10), Fill()],
            terminal_width=0,
        )

    lines = buffer.getvalue().splitlines()
    assert len(lines) == 3
    assert lines[2].endswith("x")


def test_prints_four_column_table(capsys: pytest.CaptureFixture[str]) -> None:
    print_table(
        headers=["UUID", "ID", "STATUS", "PROMPT"],
        rows=[
            ["u1", "book", "new", "first prompt"],
            ["u2", "quiz", "reviewed", "second prompt"],
        ],
        widths=[Fixed(6), Adapt(6), Adapt(8), Fill()],
        terminal_width=60,
    )

    lines = capsys.readouterr().out.splitlines()
    assert lines[0].split() == ["UUID", "ID", "STATUS", "PROMPT"]
    assert set(lines[1]) == {"-"}
    assert len(lines[1]) == len(lines[0])
    assert lines[2].split(maxsplit=3) == ["u1", "book", "new", "first prompt"]
    assert lines[3].split(maxsplit=3) == [
        "u2",
        "quiz",
        "reviewed",
        "second prompt",
    ]


def test_fixed_column_pads_shorter_values(
    capsys: pytest.CaptureFixture[str],
) -> None:
    print_table(
        headers=["WEIGHT", "NAME"],
        rows=[["1", "x"]],
        widths=[Fixed(10), Adapt()],
        terminal_width=40,
    )

    lines = capsys.readouterr().out.splitlines()
    assert lines[0].index("NAME") == 12
    assert lines[2].index("x") == 12


def test_adapt_column_is_capped_but_does_not_truncate(
    capsys: pytest.CaptureFixture[str],
) -> None:
    print_table(
        headers=["ID", "NAME", "VALUE"],
        rows=[["1", "abcdefghij", "x"]],
        widths=[Fixed(2), Adapt(4), Fill()],
        terminal_width=40,
    )

    lines = capsys.readouterr().out.splitlines()
    # The header keeps the capped width, so VALUE starts at 2 + 2 + 4 + 2.
    assert lines[0].index("VALUE") == 10
    # Overlong values overflow into the gap instead of being truncated.
    assert "abcdefghij" in lines[2]
    # x starts at 2 + 2 + 10 + 2
    assert lines[2].index("x") == 16


def test_prints_headers_when_there_are_no_rows(
    capsys: pytest.CaptureFixture[str],
) -> None:
    print_table(
        headers=["ID", "NAME", "VALUE"],
        rows=[],
        widths=[Fixed(4), Adapt(10), Fill()],
        terminal_width=40,
    )

    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 2
    assert lines[0].split() == ["ID", "NAME", "VALUE"]


def test_rejects_empty_headers() -> None:
    with pytest.raises(ValueError, match="at least one column"):
        print_table(
            headers=[],
            rows=[],
            widths=[],
            terminal_width=40,
        )


def test_rejects_missing_width_spec() -> None:
    with pytest.raises(ValueError, match="one width spec per column"):
        print_table(
            headers=["ID", "NAME"],
            rows=[["1", "a"]],
            widths=[Fixed(4)],
            terminal_width=40,
        )


def test_rejects_row_with_missing_cell() -> None:
    with pytest.raises(ValueError, match="one cell per column"):
        print_table(
            headers=["ID", "NAME"],
            rows=[["1"]],
            widths=[Fixed(4), Adapt()],
            terminal_width=40,
        )


def test_rejects_fill_column_before_the_last_position() -> None:
    with pytest.raises(ValueError, match="must be the last column"):
        print_table(
            headers=["ID", "NAME", "VALUE"],
            rows=[["1", "a", "x"]],
            widths=[Fill(), Adapt(), Adapt()],
            terminal_width=40,
        )
