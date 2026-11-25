import tomllib
from pathlib import Path

CONFIGS = ("mise.toml", "mise.private.toml")


def secret_writers(root: Path) -> list[str]:
    """Each `[dotfiles]` entry that would write a secret into a file, as `config: target`."""
    found: list[str] = []
    for name in CONFIGS:
        path = root / name
        if not path.is_file():
            continue
        entries = tomllib.loads(path.read_text()).get("dotfiles", {})
        for target, entry in entries.items():
            if isinstance(entry, dict) and _writes_secret(root, entry):
                found.append(f"{name}: {target}")
    return found


def _writes_secret(root: Path, entry: dict[str, object]) -> bool:
    if entry.get("mode") == "fnox":
        return True
    source = root / str(entry.get("source", ""))
    return (
        entry.get("mode") == "template"
        and source.is_file()
        and "secret(" in source.read_text()
    )
