# Exercise Library

## Installation

Clone the repository:
```bash
git clone <repository-url>
cd exercise-library
```

Install with `uv`:

```bash
uv tool install .
```

## Shell completion

`exercise-library` can generate shell completion scripts using `shtab`.

### Bash example

Generate and install the completion script for your user:

```bash
mkdir -p ~/.local/share/bash-completion/completions

exercise-library --print-completion bash \
    > ~/.local/share/bash-completion/completions/exercise-library
```

Restart your shell to load the completion.

To test it immediately without restarting:

```bash
source ~/.local/share/bash-completion/completions/exercise-library
```

You can also load the completion temporarily without installing it:

```bash
eval "$(exercise-library --print-completion bash)"
```

This only applies to the current shell session.
