"""Temporary: finds what fills the uv cache between Update runs. Remove once the cause is fixed."""

import os
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

GIB = 1024**3
# Throwaway environments and builds should be near empty between runs; the whole cache should not jump
ENV_DIRS = ("environments-v2", "builds-v0")
ENV_LIMIT_BYTES = 1 * GIB
ENV_LIMIT_FILES = 50_000
GROWTH_LIMIT_BYTES = 5 * GIB
_DIST = re.compile(r"^(.+?)-[0-9][^-]*\.dist-info$")


@dataclass
class Usage:
    bytes: int = 0
    files: int = 0


@dataclass
class Entry:
    path: str
    bytes: int
    files: int
    mtime: float
    packages: list[str] = field(default_factory=list)


def _walk(path: Path) -> tuple[Usage, list[str]]:
    usage, packages = Usage(), []
    for top, dirs, files in os.walk(path):
        packages += [m[1] for d in dirs if (m := _DIST.match(d))]
        for name in files:
            try:
                usage.bytes += os.lstat(os.path.join(top, name)).st_size
            except OSError:
                continue
            usage.files += 1
    return usage, sorted(set(packages))


def snapshot(cache: Path, since: float | None) -> dict[str, Any]:
    """Each folder's size, every environment and build, and the packages unpacked since `since`."""
    folders: dict[str, Usage] = {}
    entries: dict[str, list[Entry]] = {d: [] for d in ENV_DIRS}
    unpacked: Counter[str] = Counter()
    for folder in sorted(p for p in cache.iterdir() if p.is_dir()):
        total = Usage()
        for child in folder.iterdir():
            usage, packages = (
                _walk(child)
                if child.is_dir()
                else (Usage(child.lstat().st_size, 1), [])
            )
            total.bytes += usage.bytes
            total.files += usage.files
            mtime = child.lstat().st_mtime
            if folder.name in entries:
                entries[folder.name].append(
                    Entry(
                        str(child.relative_to(cache)),
                        usage.bytes,
                        usage.files,
                        mtime,
                        packages,
                    )
                )
            elif folder.name == "archive-v0" and since is not None and mtime > since:
                unpacked.update(packages)
        folders[folder.name] = total
    return {
        "folders": {k: asdict(v) for k, v in folders.items()},
        "entries": {
            k: [asdict(e) for e in sorted(v, key=lambda e: -e.bytes)]
            for k, v in entries.items()
        },
        "unpacked_since_last": dict(unpacked.most_common(30)),
    }


def total_bytes(snap: dict[str, Any]) -> int:
    return sum(f["bytes"] for f in snap["folders"].values())


def problems(previous: dict[str, Any] | None, current: dict[str, Any]) -> list[str]:
    found = []
    for name in ENV_DIRS:
        usage = current["folders"].get(name, {"bytes": 0, "files": 0})
        if usage["bytes"] > ENV_LIMIT_BYTES or usage["files"] > ENV_LIMIT_FILES:
            found.append(
                f"{name} holds {usage['bytes'] / GIB:.1f} GiB in {usage['files']} files"
            )
    if previous is not None:
        grew = total_bytes(current) - total_bytes(previous)
        if grew > GROWTH_LIMIT_BYTES:
            found.append(f"the cache grew {grew / GIB:.1f} GiB since the last run")
    return found
