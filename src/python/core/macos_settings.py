import hashlib
import os
from pathlib import Path


def scripts(root: Path) -> list[Path]:
    """The public then private settings scripts, one per area, each in name order."""
    return [
        script
        for folder in (root / "src/lib/macos", root / "private/src/lib/macos")
        if folder.is_dir()
        for script in sorted(folder.glob("*.sh"))
    ]


def stamp_dir() -> Path:
    state = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local/state")
    return Path(state) / "dotfiles" / "macos"


def stamp(root: Path, script: Path) -> Path:
    return stamp_dir() / f"{script.relative_to(root)}.sha256"


def digest(script: Path) -> str:
    return hashlib.sha256(script.read_bytes()).hexdigest()


def changed(root: Path, script: Path) -> bool:
    """True when the script has not run successfully since its content last changed."""
    path = stamp(root, script)
    return not path.is_file() or path.read_text().strip() != digest(script)


def record(root: Path, script: Path) -> None:
    path = stamp(root, script)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(digest(script) + "\n")
