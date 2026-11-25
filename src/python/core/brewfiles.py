import re
from collections.abc import Sequence
from pathlib import Path

from src.python.core import machines

# A Brewfile holds casks only (ADR 0002), plus mise: the bootstrap, so Update upgrades it
CASK_LINE = re.compile(r"""^(cask (["'])[^"']+\2(,.*)?|brew (["'])mise\4)$""")


def paths(root: Path, roles: Sequence[str] = ()) -> list[Path]:
    """The public and private Brewfiles, then the private `Brewfile.<role>` of each role given."""
    candidates = (root / "src/lib/Brewfile", root / "private/src/lib/Brewfile")
    return [
        *(p for p in candidates if p.is_file()),
        *machines.role_files(root, "Brewfile.{}", roles),
    ]


def every_path(root: Path) -> list[Path]:
    """Every Brewfile, each role's included, whatever this machine is."""
    return [*paths(root), *sorted(machines.lib(root).glob("Brewfile.*"))]


def line_allowed(line: str) -> bool:
    text = line.strip()
    return not text or text.startswith("#") or bool(CASK_LINE.match(text))
