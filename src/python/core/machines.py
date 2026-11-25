import json
import re
import tomllib
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

ROLE = re.compile(r"[a-z0-9][a-z0-9-]*")
NAME = ROLE
SERIAL = re.compile(r'"IOPlatformSerialNumber" = "([^"]+)"')
LINUX_IDS = (Path("/etc/machine-id"), Path("/var/lib/dbus/machine-id"))
ENTRY = '{ name = "<name>", roles = ["<role>", ...] } (lowercase letters, digits, -)'


@dataclass(frozen=True)
class Machine:
    name: str
    roles: list[str] = field(default_factory=list)


def lib(root: Path) -> Path:
    # a serial and its name and roles say whose machine it is, so the list and role files are private
    return root / "private/src/lib"


def path(root: Path) -> Path:
    return lib(root) / "machines.toml"


def serial(ioreg: str) -> str | None:
    """The serial number in `ioreg -rd1 -c IOPlatformExpertDevice` output."""
    found = SERIAL.search(ioreg)
    return found[1] if found else None


def linux_id(files: Sequence[Path] = LINUX_IDS) -> str | None:
    """The systemd machine ID, the Linux key in the machine list."""
    return next(
        (t for p in files if p.is_file() and (t := p.read_text().strip())), None
    )


def _valid(entry: object) -> bool:
    if not isinstance(entry, dict) or set(entry) - {"name", "roles"}:
        return False
    name, roles = entry.get("name"), entry.get("roles", [])
    return (
        isinstance(name, str)
        and bool(NAME.fullmatch(name))
        and isinstance(roles, list)
        and all(isinstance(r, str) and ROLE.fullmatch(r) for r in roles)
    )


def machine_list(root: Path) -> dict[str, Machine]:
    """The private `"<machine id>" = { name = ..., roles = [...] }` map; empty when there is none."""
    file = path(root)
    if not file.is_file():
        return {}
    found = tomllib.loads(file.read_text())
    for key, entry in found.items():
        if not _valid(entry):
            raise SystemExit(f"{file}: {key!r} needs {ENTRY}")
    return {k: Machine(e["name"], e.get("roles", [])) for k, e in found.items()}


def roles(root: Path, machine_id: str | None) -> list[str]:
    """This machine's roles; an unlisted machine has none."""
    found = machine_list(root).get(machine_id or "")
    return found.roles if found else []


def name(root: Path, machine_id: str | None) -> str | None:
    """This machine's name; an unlisted machine has none."""
    found = machine_list(root).get(machine_id or "")
    return found.name if found else None


def add(root: Path, machine_id: str, new_name: str) -> Path:
    """Adds this machine to the list under a new name, with no roles."""
    if not NAME.fullmatch(new_name):
        raise ValueError(f"{new_name!r}: use lowercase letters, digits and -")
    listed = machine_list(root)
    if machine_id in listed:
        raise ValueError(f"this machine is already named {listed[machine_id].name!r}")
    if any(m.name == new_name for m in listed.values()):
        raise ValueError(f"{new_name!r} already names another machine")
    file = path(root)
    if not file.parent.is_dir():
        raise SystemExit(
            f"{file.parent} is missing, so there is nowhere to save the name"
        )
    text = file.read_text() if file.is_file() else ""
    sep = "" if not text or text.endswith("\n") else "\n"
    file.write_text(
        f'{text}{sep}{json.dumps(machine_id)} = {{ name = "{new_name}" }}\n'
    )
    return file


def role_files(root: Path, pattern: str, roles: Sequence[str]) -> list[Path]:
    """The file `pattern` names (`{}` is the role) of each role that has one."""
    return [p for r in roles if (p := lib(root) / pattern.format(r)).is_file()]


def unknown_roles(root: Path) -> list[str]:
    """Roles in the machine list with neither a `Brewfile.<role>` nor a `keep.<role>.toml`."""
    named = dict.fromkeys(r for m in machine_list(root).values() for r in m.roles)
    return [
        r
        for r in named
        if not role_files(root, "Brewfile.{}", [r])
        and not role_files(root, "keep.{}.toml", [r])
    ]
