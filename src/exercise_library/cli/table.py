import shutil

_COLUMN_GAP = "  "
_ELLIPSIS = "..."
_MIN_THIRD_WIDTH = 20


def print_three_column_table(
    first_col_width: int,
    second_col_max: int,
    headers: list[str],
    rows: list[list[str]],
    terminal_width: int | None = None,
) -> None:
    """Print a fixed-width table suited to the current terminal width.

    Column 0 is fixed width, column 1 adapts up to ``second_col_max``, and
    column 2 fills the remaining width (truncated with ellipsis).
    ``terminal_width`` defaults to the current terminal; passing it
    explicitly keeps this function pure and easily testable.
    """
    assert len(headers) == 3

    second_width = max(len(row[1]) for row in rows + [headers])
    second_width = min(second_width, second_col_max)

    if terminal_width is None:
        terminal_width = shutil.get_terminal_size().columns - 1

    third_width = max(
        _MIN_THIRD_WIDTH,
        terminal_width - first_col_width - second_width - (2 * len(_COLUMN_GAP)),
    )

    rows = [row[:] for row in rows]
    for row in rows:
        if len(row[2]) > third_width:
            row[2] = row[2][: third_width - len(_ELLIPSIS)] + _ELLIPSIS

    header_line = (
        f"{headers[0]:<{first_col_width}}{_COLUMN_GAP}"
        f"{headers[1]:<{second_width}}{_COLUMN_GAP}{headers[2]}"
    )
    print(header_line)
    print("-" * len(header_line))

    for row in rows:
        print(
            f"{row[0]:<{first_col_width}}{_COLUMN_GAP}"
            f"{row[1]:<{second_width}}{_COLUMN_GAP}{row[2]}"
        )
