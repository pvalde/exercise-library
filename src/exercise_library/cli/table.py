import shutil
from dataclasses import dataclass

_COLUMN_GAP = "  "
_ELLIPSIS = "..."
_DEFAULT_FILL_MIN_WIDTH = 20


@dataclass(frozen=True)
class Fixed:
    """Pad the column to exactly ``width`` characters."""

    width: int


@dataclass(frozen=True)
class Adapt:
    """Pad the column to its longest value, capped at ``max_width``."""

    max_width: int | None = None


@dataclass(frozen=True)
class Fill:
    """Take the remaining width and truncate overflowing values.

    ``min_width`` floors the column so a narrow terminal still yields a
    readable table instead of a negative width.
    """

    min_width: int = _DEFAULT_FILL_MIN_WIDTH


ColumnWidth = Fixed | Adapt | Fill


def print_table(
    headers: list[str],
    rows: list[list[str]],
    widths: list[ColumnWidth],
    terminal_width: int | None = None,
) -> None:
    """Print a table suited to the current terminal width.

    Each column declares how its width is chosen: ``Fixed`` pads to an
    exact width, ``Adapt`` pads to the column's longest value (values
    longer than the cap overflow), and ``Fill`` takes the remaining
    width and truncates its values with an ellipsis. A ``Fill`` column
    is only allowed in the last position, which is left unpadded.
    ``terminal_width`` defaults to the current terminal; passing it
    explicitly keeps this function pure and easily testable.

    Raises ``ValueError`` when headers, rows and widths do not describe
    the same number of columns or a ``Fill`` column is not last.
    """
    if not headers:
        raise ValueError("a table needs at least one column")
    if len(headers) != len(widths):
        raise ValueError("one width spec per column")
    if any(len(row) != len(widths) for row in rows):
        raise ValueError("one cell per column")
    if any(
        isinstance(spec, Fill) and index != len(widths) - 1
        for index, spec in enumerate(widths)
    ):
        raise ValueError("a Fill column must be the last column")

    if terminal_width is None:
        terminal_width = shutil.get_terminal_size().columns - 1

    column_widths = _column_widths(headers, rows, widths, terminal_width)
    last_index = len(widths) - 1
    last_is_fill = isinstance(widths[last_index], Fill)

    header_line = _format_row(headers, column_widths, last_is_fill)
    print(header_line)
    print("-" * len(header_line))

    for row in rows:
        print(_format_row(row, column_widths, last_is_fill))


def _column_widths(
    headers: list[str],
    rows: list[list[str]],
    widths: list[ColumnWidth],
    terminal_width: int,
) -> list[int]:
    column_widths: list[int] = []
    for index, spec in enumerate(widths):
        if isinstance(spec, Fill):
            used = sum(column_widths) + index * len(_COLUMN_GAP)
            column_widths.append(max(spec.min_width, terminal_width - used))
        elif isinstance(spec, Fixed):
            column_widths.append(spec.width)
        else:
            longest = max(len(cells[index]) for cells in [*rows, headers])
            column_widths.append(
                longest if spec.max_width is None else min(longest, spec.max_width)
            )
    return column_widths


def _format_row(cells: list[str], column_widths: list[int], last_is_fill: bool) -> str:
    last_index = len(column_widths) - 1
    last_cell = cells[last_index]
    if last_is_fill and len(last_cell) > column_widths[last_index]:
        last_cell = last_cell[: column_widths[last_index] - len(_ELLIPSIS)] + _ELLIPSIS

    padded = [f"{cells[index]:<{column_widths[index]}}" for index in range(last_index)]
    padded.append(last_cell)
    return _COLUMN_GAP.join(padded)
