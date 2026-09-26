import tempfile
import webbrowser
from collections.abc import Mapping, MutableMapping, Sequence
from html import escape
from pathlib import Path
from typing import Any
from uuid import UUID

from markdown_it import MarkdownIt, token
from mdit_py_plugins.dollarmath import dollarmath_plugin
from mdit_py_plugins.texmath import texmath_plugin

from exercise_library.application import ExerciseApplication
from exercise_library.cli.exceptions import CLIError
from exercise_library.models import Exercise


class ShowError(CLIError):
    pass


def show_exercise(
    application: ExerciseApplication,
    uuid: UUID | None = None,
    identifier: str | None = None,
    show_prompt: bool = False,
    show_answer: bool = False,
    show_in_webbrowser: bool = False,
) -> None:
    if uuid is None and identifier is None:
        raise ShowError("At least one of 'uuid' or 'identifier' must be provided.")

    if uuid:
        exercise = application.get_exercise_by_uuid(uuid)
    else:
        assert identifier is not None
        exercise = application.get_exercise_by_identifier(identifier)

    if show_in_webbrowser:
        _open_webbrowser(
            exercise,
            show_prompt=show_prompt,
            show_answer=show_answer,
        )

    else:
        output = ""

        if exercise.identifier:
            output += f"Exercise:\n{exercise.identifier}\n\n"
        else:
            output += f"Exercise:\n{exercise.uuid}\n\n"

        if show_prompt:
            output += f"Prompt:\n{exercise.prompt}\n\n"

        if show_answer:
            output += f"Answer:\n{exercise.answer}\n"

        print(output)


def _open_webbrowser(
    exercise: Exercise,
    show_prompt: bool = False,
    show_answer: bool = False,
) -> None:
    md = MarkdownIt(
        "commonmark",
        {
            "html": True,
            "breaks": True,
        },
    )
    md.use(texmath_plugin, delimiters="brackets")
    md.use(dollarmath_plugin)

    def render_math_inline(
        self: Any,
        tokens: Sequence[token.Token],
        idx: int,
        options: Mapping[str, Any],
        env: MutableMapping[str, Any],
    ) -> Any:
        return "$" + tokens[idx].content + "$"

    def render_math_block(
        self: Any,
        tokens: Sequence[token.Token],
        idx: int,
        options: Mapping[str, Any],
        env: MutableMapping[str, Any],
    ) -> Any:
        return "$$" + tokens[idx].content + "$$"

    md.add_render_rule("math_inline", render_math_inline)
    md.add_render_rule("math_block", render_math_block)

    prompt_html = md.render(exercise.prompt)
    answer_html = md.render(exercise.answer)

    assert exercise.uuid is not None

    title = (
        "<title>" + escape(exercise.identifier) + "</title>\n"
        if exercise.identifier
        else "<title>" + escape(str(exercise.uuid)) + "</title>\n"
    )

    h1 = (
        (
            '<section class="ex_uuid">\n'
            + "<h2><i>"
            + escape(exercise.identifier)
            + "</i></h2>\n"
            + "\n"
            + "</section>\n"
        )
        if exercise.identifier
        else (
            '<section class="ex_uuid">\n'
            + "<h1>Title</h1>\n"
            + escape(str(exercise.uuid))
            + "\n"
            + "</section>\n"
        )
    )

    prompt_section = (
        (
            '<section class="prompt">\n'
            + "<h2>Prompt</h2>\n"
            + prompt_html
            + "\n"
            + "</section>\n"
        )
        if show_prompt
        else ""
    )

    answer_section = (
        (
            '<section class="answer">\n'
            + "<h2>Answer</h2>\n"
            + answer_html
            + "\n"
            + "</section>\n"
        )
        if show_answer
        else ""
    )

    html = (
        "<!DOCTYPE html>\n"
        + "<html>\n"
        + "<head>\n"
        + '<meta charset="utf-8">\n'
        + title
        + "\n"
        + "<script>\n"
        + "window.MathJax = {\n"
        + "    tex: {\n"
        + "        inlineMath: [\n"
        + "            ['$', '$'],\n"
        + "            ['\\\\(', '\\\\)'],\n"
        + "        ],\n"
        + "        displayMath: [\n"
        + "            ['$$', '$$'],\n"
        + "            ['\\\\[', '\\\\]']\n"
        + "        ]\n"
        + "    }\n"
        + "};\n"
        + "</script>\n"
        + "\n"
        + '<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>\n'
        + "\n"
        + "<style>\n"
        + "body {\n"
        + "    max-width: 900px;\n"
        + "    margin: 40px auto;\n"
        + "    padding: 0 20px;\n"
        + "    font-family: system-ui, sans-serif;\n"
        + "    line-height: 1.6;\n"
        + "}\n"
        + "\n"
        + ".prompt {\n"
        + "    border-bottom: 1px solid #ccc;\n"
        + "    padding-bottom: 30px;\n"
        + "    margin-bottom: 30px;\n"
        + "}\n"
        + "\n"
        + "pre {\n"
        + "    background: #f5f5f5;\n"
        + "    padding: 1em;\n"
        + "    overflow-x: auto;\n"
        + "}\n"
        + "\n"
        + "code {\n"
        + "    font-family: monospace;\n"
        + "}\n"
        + "\n"
        + "blockquote {\n"
        + "    border-left: 4px solid #ccc;\n"
        + "    padding-left: 1em;\n"
        + "    color: #666;\n"
        + "}\n"
        + "</style>\n"
        + "\n"
        + "</head>\n"
        + "<body>\n"
        + "\n"
        + h1
        + prompt_section
        + answer_section
        + "</body>\n"
        + "</html>\n"
    )

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".html",
        prefix="exercise-",
        delete=False,
        encoding="utf-8",
    ) as file:
        file.write(html)
        file.close()

        webbrowser.open(Path(file.name).as_uri())
