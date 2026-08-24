import os
import shlex
import subprocess
import sys
import tempfile

from exercise_library.config import APP_NAME


def edit_in_editor(field_name: str) -> str:
    editor = os.environ.get("VISUAL") or os.environ.get("EDITOR")
    if not editor:
        print("Error: Neither $VISUAL nor $EDITOR environment variable is set.")
        sys.exit(1)

    initial_content = (
        f"<!-- [{APP_NAME}]: Enter the exercise {field_name}"
        + " below using Markdown. -->\n"
        f"<!-- [{APP_NAME}]: This comment will be automatically removed. -->\n\n"
    )

    with tempfile.NamedTemporaryFile(
        mode="w+",
        suffix=".md",
        delete=False,
        encoding="utf-8",
    ) as tf:
        tf.write(initial_content)
        tf_name = tf.name

    try:
        subprocess.run(shlex.split(editor) + [tf_name], check=True)

        with open(tf_name, encoding="utf-8") as tf:
            content = tf.read()

        if content == initial_content:
            return ""

        lines = content.splitlines(keepends=True)

        # Filter out generated HTML comment lines.
        content = "".join(
            line for line in lines if not line.strip().startswith(f"<!-- [{APP_NAME}]:")
        ).strip()

        return content

    except subprocess.CalledProcessError:
        print("Error: Editor exited with a non-zero status.")
        return ""

    finally:
        if os.path.exists(tf_name):
            os.unlink(tf_name)
