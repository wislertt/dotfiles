from collections.abc import Iterable
from pathlib import Path

from identify import identify


def classify(names: Iterable[str]) -> tuple[list[str], list[str]]:
    """Split files into sh-family scripts (for ShellCheck) and zsh scripts (for `zsh -n`)."""
    tags = {
        name: identify.tags_from_path(name)
        for name in names
        if Path(name).is_file() and not Path(name).is_symlink()
    }
    sh = [n for n, t in tags.items() if "shell" in t and "zsh" not in t]
    zsh = [n for n, t in tags.items() if "zsh" in t]
    return sh, zsh
