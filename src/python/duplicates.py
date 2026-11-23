import os
import tomllib
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Copy:
    tool: str
    binary: str
    path: Path


def declared_mise_tools(root: Path) -> set[str]:
    """The `[tools]` keys, in the form `mise bin-paths` takes (for example `npm:oxfmt`)."""
    keys: set[str] = set()
    for filename in ("mise.toml", "mise.private.toml"):
        path = root / filename
        if path.is_file():
            keys |= set(tomllib.loads(path.read_text()).get("tools", {}))
    return keys


def _is_executable(path: Path) -> bool:
    return path.is_file() and os.access(path, os.X_OK)


def other_copies(
    tool_bins: Mapping[str, Sequence[Path]],
    path: Iterable[Path],
    ignore: Iterable[Path],
) -> list[Copy]:
    """Executables on PATH that share a name with one a declared tool ships, outside its own folders."""
    skip = set(ignore)
    dirs = list(dict.fromkeys(path))
    found: list[Copy] = []
    for tool, own in tool_bins.items():
        names = sorted(
            {
                p.name
                for d in own
                if d.is_dir()
                for p in d.iterdir()
                if _is_executable(p)
            }
        )
        for name in names:
            found += [
                Copy(tool, name, d / name)
                for d in dirs
                if d not in own and d not in skip and _is_executable(d / name)
            ]
    return found
