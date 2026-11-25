import json
import os
import re
import shlex
import tomllib
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from src.python.core import machines, signing


@dataclass(frozen=True)
class Stray:
    kind: str
    name: str
    remove: tuple[tuple[str, ...], ...] = ()
    manual: str | None = None

    @property
    def key(self) -> str:
        return f"{self.kind}:{self.name}"


# where Tidy looks: a label, the Stray kinds found there and the tool it needs
SOURCES: tuple[tuple[str, tuple[str, ...], str | None], ...] = (
    ("Homebrew", ("brew", "cask"), "brew"),
    ("uv tools", ("uv",), "uv"),
    ("cargo crates", ("cargo",), "cargo"),
    ("npm globals", ("npm",), "npm"),
    ("pnpm globals", ("pnpm",), "pnpm"),
    ("PATH", ("dead-link",), None),
    ("Old tool-manager folders", ("leftover",), None),
    ("~/.local/bin", ("local-bin",), None),
    ("Apps", ("app",), None),
    ("Rust toolchains", ("rust-toolchain",), "rustup"),
    ("Copies of mise tools", ("duplicate",), "mise"),
    ("GitHub signing keys", ("signing-key",), "gh"),
    ("GitHub SSH keys", ("ssh-key",), "gh"),
)

# most machines have no Rust, so its absence is not worth a line
QUIET_WHEN_MISSING = frozenset({"rustup"})


def cache_cleaners(
    volumes: bool, is_macos: bool
) -> tuple[tuple[str, str, tuple[str, ...]], ...]:
    """What `--caches` runs: a label, the tool it needs and the command."""
    docker = ("docker", "system", "prune", "--all", "--force")
    return (
        ("Docker", "docker", (*docker, "--volumes") if volumes else docker),
        # without a terminal Mole skips the system caches that need sudo
        *((("Mole", "mo", ("mo", "clean")),) if is_macos else ()),
    )


# what to do about a Stray bake leaves to the owner, by kind
NEEDS_YOU = {
    "dead-link": "in a folder that needs sudo",
    "leftover": "outside home, so it needs sudo",
    "local-bin": "not from this repo and may hold credentials, so bake leaves it",
    "app": "not installed by a cask: put it in a Brewfile or keep it",
    "duplicate": "uninstall it with the manager that owns the folder",
    "signing-key": "never expires, so it may have been added by hand",
    "ssh-key": "git uses HTTPS, so a GitHub SSH key is unused unless you keep it",
}


def check_report(strays: Sequence[Stray]) -> list[str]:
    """`bake tidy --check` output: what plain `bake tidy` removes, then the rest grouped by kind with the command to run."""
    removable = [s for s in strays if s.remove]
    needs_you = [s for s in strays if not s.remove]
    lines: list[str] = []
    if removable:
        lines += [f"Removed by `bake tidy` ({len(removable)})"]
        lines += [f"  {s.key}" for s in removable]
    if needs_you:
        if lines:
            lines.append("")
        lines.append(
            f"Needs you ({len(needs_you)}): run the command, or keep it with"
            ' "kind:name" = "reason" in src/lib/keep.toml'
        )
        for kind in dict.fromkeys(s.kind for s in needs_you):
            group = [s for s in needs_you if s.kind == kind]
            width = max(len(s.key) for s in group)
            hint = NEEDS_YOU.get(kind)
            lines += ["", f"{kind} ({len(group)})" + (f": {hint}" if hint else "")]
            lines += [
                f"  {s.key:{width}}  {s.manual}".rstrip() if s.manual else f"  {s.key}"
                for s in group
            ]
    return lines


def keep_list(root: Path, roles: Sequence[str] = ()) -> dict[str, str]:
    """The `kind:name = "reason"` entries of the public and private Keep lists and each role's `keep.<role>.toml`."""
    keep: dict[str, str] = {}
    for path in (
        root / "src/lib/keep.toml",
        root / "private/src/lib/keep.toml",
        *machines.role_files(root, "keep.{}.toml", roles),
    ):
        if not path.is_file():
            continue
        for key, reason in tomllib.loads(path.read_text()).items():
            kind, _, name = key.partition(":")
            if not (kind and name and isinstance(reason, str) and reason.strip()):
                raise SystemExit(
                    f'{path}: {key!r} needs a "kind:name" key and a one-line reason'
                )
            keep[key] = reason
    return keep


def cleanup_listing(listing: str) -> dict[str, list[str]]:
    """Names under each `Would uninstall casks:` / `formulae:` heading of `brew bundle cleanup` without `--force`."""
    found: dict[str, list[str]] = {"casks": [], "formulae": []}
    section: list[str] | None = None
    for line in listing.splitlines():
        if line.endswith(":") or line.startswith(("Would ", "Run ")):
            section = found.get(line.removeprefix("Would uninstall ").rstrip(":"))
        elif section is not None and line.strip():
            section.append(line.strip())
    return found


# npm ships these with node itself
NODE_BUNDLED = frozenset({"npm", "corepack"})


def uv_tools(listing: str) -> list[str]:
    """Tool names from `uv tool list`; its `- binary` lines are skipped."""
    return [
        line.split()[0]
        for line in listing.splitlines()
        if line.strip() and not line.startswith(("-", " ", "No tools"))
    ]


def cargo_crates(listing: str) -> list[str]:
    """Crate names from `cargo install --list`; indented lines are binaries."""
    return [
        line.split()[0]
        for line in listing.splitlines()
        if line.strip() and not line[0].isspace()
    ]


def npm_globals(listing: str) -> list[str]:
    """Package names from `npm ls -g --depth=0 --json`, minus what node ships."""
    deps = json.loads(listing or "{}").get("dependencies", {})
    return [name for name in deps if name not in NODE_BUNDLED]


def pnpm_globals(listing: str) -> list[str]:
    """Package names from `pnpm ls -g --json`, a list of global projects."""
    return [
        name
        for project in json.loads(listing or "[]")
        for name in project.get("dependencies", {})
    ]


# Old tool managers mise replaced; a hand-installed Go lives outside home
HOME_LEFTOVERS = (
    ".asdf",
    ".pyenv",
    ".nvm",
    ".bun",
    ".volta",
    ".fnm",
    ".conda",
    "miniconda3",
    "anaconda3",
    "miniforge3",
)
SYSTEM_LEFTOVERS = (Path("/usr/local/go"),)


def _show(path: Path, home: Path) -> str:
    return f"~/{path.relative_to(home)}" if path.is_relative_to(home) else str(path)


def _by_hand(*cmd: str | Path) -> str:
    return shlex.join(map(str, cmd))


def filesystem_strays(
    path_dirs: Sequence[Path], home: Path, system: Iterable[Path]
) -> list[Stray]:
    """Dead links on PATH, leftover tool-manager folders and unknown local bin files."""
    dirs = list(dict.fromkeys(path_dirs))
    strays: list[Stray] = []
    skip = set(system)
    for d in dirs:
        if not d.is_dir() or d in skip:
            continue
        writable = os.access(d, os.W_OK)
        strays += [
            Stray(
                "dead-link",
                _show(link, home),
                remove=(("rm", str(link)),) if writable else (),
                manual=None if writable else _by_hand("sudo", "rm", link),
            )
            for link in sorted(
                p for p in d.iterdir() if p.is_symlink() and not p.exists()
            )
        ]
    for folder in (home / name for name in HOME_LEFTOVERS):
        if folder.exists():
            strays.append(
                Stray(
                    "leftover",
                    _show(folder, home),
                    # read-only caches (conda, module caches) otherwise stop the removal halfway
                    remove=(
                        ("chmod", "-R", "u+w", str(folder)),
                        ("rm", "-rf", str(folder)),
                    ),
                )
            )
    strays += [
        Stray("leftover", str(folder), manual=_by_hand("sudo", "rm", "-rf", folder))
        for folder in SYSTEM_LEFTOVERS
        if folder.exists()
    ]
    local_bin = home / ".local" / "bin"
    if local_bin.is_dir():
        # may hold credentials, so bake never reads or deletes it
        strays += [
            Stray("local-bin", p.name, manual=_by_hand("rm", p))
            for p in sorted(local_bin.iterdir())
            if p.is_file() and not p.is_symlink()
        ]
    return strays


@dataclass(frozen=True)
class Copy:
    tool: str
    binary: str
    path: Path


def declared_mise_tools(root: Path) -> set[str]:
    """The `[tools]` keys of the repo and global mise files, in the form `mise bin-paths` takes (for example `npm:oxfmt`)."""
    keys: set[str] = set()
    for filename in (
        "mise.toml",
        "mise.private.toml",
        "src/config/mise/config.toml",
        "private/src/config/mise/config.toml",
    ):
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


def duplicate_strays(copies: Iterable[Copy], home: Path) -> list[Stray]:
    # the path names the manager that owns it; removing the copy is the owner's call
    return [Stray("duplicate", _show(c.path, home)) for c in copies]


def _strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    return [v for v in value if isinstance(v, str)] if isinstance(value, list) else []


def _uninstall_steps(cask: Mapping[str, object]) -> list[Mapping[str, object]]:
    artifacts = cask.get("artifacts")
    return [
        step
        for artifact in (artifacts if isinstance(artifacts, list) else [])
        if isinstance(artifact, dict)
        for step in artifact.get("uninstall", [])
        if isinstance(step, dict)
    ]


def _casks(info: str) -> list[dict[str, Any]]:
    return json.loads(info or "{}").get("casks", [])


def apps_owned_by_casks(info: str) -> set[str]:
    """App bundle names from `brew info --cask --installed --json=v2`: each `app` artifact and each app an uninstall deletes."""
    names: set[str] = set()
    for cask in _casks(info):
        for artifact in cask.get("artifacts", []):
            if not isinstance(artifact, dict) or "app" not in artifact:
                continue
            if target := artifact.get("target"):
                names.add(Path(target).name)
            names |= {Path(a).name for a in artifact["app"] if isinstance(a, str)}
        for step in _uninstall_steps(cask):
            names |= {
                Path(p).name for p in _strings(step.get("delete")) if p.endswith(".app")
            }
    return names


def cask_receipt_patterns(info: str) -> list[str]:
    """The `pkgutil` receipt patterns (regexes) the uninstall of each installed cask removes."""
    return list(
        dict.fromkeys(
            pattern
            for cask in _casks(info)
            for step in _uninstall_steps(cask)
            for pattern in _strings(step.get("pkgutil"))
        )
    )


def receipt_apps(files: str) -> set[str]:
    """Top-level app bundles in `pkgutil --files`, wherever the receipt says they went."""
    return {
        line.removeprefix("Applications/")
        for line in files.splitlines()
        if line.endswith(".app") and "/" not in line.removeprefix("Applications/")
    }


def app_strays(applications: Path, owned: set[str]) -> list[Stray]:
    # an app may be MDM-managed or hold data, so bake never deletes one
    return [
        Stray("app", app.stem, manual=_by_hand("rm", "-rf", app))
        for app in sorted(applications.glob("*.app"))
        if app.name not in owned
    ]


def signing_key_strays(
    keys: Iterable[signing.GithubKey], this_machine: str | None, now: datetime
) -> list[Stray]:
    """Expired GitHub GPG keys are deleted; one that never expires may have been added by hand, so it is only named."""
    strays: list[Stray] = []
    for key in keys:
        state = signing.status(key, this_machine, now)
        delete = ("gh", "api", "-X", "DELETE", f"user/gpg_keys/{key.id}")
        name = key.name or key.key_id
        if state == "expired":
            # the stored gh login has the admin:gpg_key scope; a token in the shell may not
            unset = [arg for var in signing.GH_TOKEN_VARS for arg in ("-u", var)]
            strays.append(
                Stray("signing-key", name, remove=(("env", *unset, *delete),))
            )
        elif state == "no expiry":
            strays.append(Stray("signing-key", name, manual=_by_hand(*delete)))
    return strays


_TOOLCHAIN = re.compile(
    r"(?P<channel>stable|beta|nightly|\d+\.\d+(?:\.\d+)?)"
    r"(?:-(?P<date>\d{4}-\d{2}-\d{2}))?(?:-(?P<host>.+))?"
)
CHANNELS = frozenset({"stable", "beta", "nightly"})


PIN_FILES = ("rust-toolchain.toml", "rust-toolchain")


def repos_roots(root: Path) -> list[Path]:
    """The folders `src/lib/tidy.toml` names under `repos`, where Tidy looks for Rust pins."""
    path = root / "src/lib/tidy.toml"
    if not path.is_file():
        return []
    repos = tomllib.loads(path.read_text()).get("repos", [])
    if not (isinstance(repos, list) and all(isinstance(r, str) for r in repos)):
        raise SystemExit(f"{path}: repos needs to be a list of folders")
    return [Path(r).expanduser() for r in repos]


def _pinned_channel(path: Path) -> str | None:
    try:
        text = path.read_text()
    except OSError, UnicodeDecodeError:
        return None
    try:
        table = tomllib.loads(text).get("toolchain")
        channel = table.get("channel") if isinstance(table, dict) else None
    except tomllib.TOMLDecodeError:
        # the legacy file may hold just the channel
        channel = next(
            (line.strip() for line in text.splitlines() if line.strip()), None
        )
    return channel if isinstance(channel, str) else None


def rust_pins(roots: Iterable[Path]) -> set[str]:
    """Channels pinned at repo roots one or two folders below each repos root; deeper pins are not read, to keep the scan cheap."""
    return {
        channel
        for root in roots
        for pattern in ("*", "*/*")
        for name in PIN_FILES
        for path in root.glob(f"{pattern}/{name}")
        if path.is_file() and (channel := _pinned_channel(path))
    }


def _channel(name: str) -> str | None:
    """The channel and any date of a toolchain or pin, without the host."""
    match = _TOOLCHAIN.fullmatch(name)
    if not match:
        return None
    return match["channel"] + (f"-{match['date']}" if match["date"] else "")


def _is_pinned(channel: str, pins: Iterable[str]) -> bool:
    for pin in filter(None, map(_channel, pins)):
        # rustup resolves a pin like 1.100 to some 1.100.x
        if channel == pin or (pin.count(".") == 1 and channel.startswith(f"{pin}.")):
            return True
    return False


def rust_toolchain_strays(listing: str, pins: Iterable[str]) -> list[Stray]:
    """Numbered and dated toolchains from `rustup toolchain list` that no repo pins; channels and custom toolchains are left alone."""
    pins = list(pins)
    return [
        Stray(
            "rust-toolchain", name, remove=(("rustup", "toolchain", "uninstall", name),)
        )
        for name in (line.split()[0] for line in listing.splitlines() if line.strip())
        if (channel := _channel(name))
        and channel not in CHANNELS
        and not _is_pinned(channel, pins)
    ]


# the stored gh login has the key scopes; a token in the shell may not
_WITH_STORED_GH_LOGIN = ("env", *(a for v in signing.GH_TOKEN_VARS for a in ("-u", v)))


def ssh_key_strays(listing: str) -> list[Stray]:
    """Every SSH login key from `gh api --paginate --slurp user/keys`; a key was added by hand, so it is only named."""
    return [
        Stray(
            "ssh-key",
            key.get("title") or str(key["id"]),
            manual=_by_hand(
                *_WITH_STORED_GH_LOGIN, "gh", "ssh-key", "delete", key["id"], "--yes"
            ),
        )
        for page in json.loads(listing or "[]")
        for key in page
    ]
