import json
import os
import re
import tomllib
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


class Manager(Protocol):
    name: str

    @property
    def binary(self) -> str: ...

    def installed(self) -> set[str]: ...

    def uninstall(self, name: str) -> bool: ...


@dataclass(frozen=True)
class Duplicate:
    manager: str
    name: str


@dataclass
class Report:
    duplicates: list[Duplicate] = field(default_factory=list)
    removed: list[Duplicate] = field(default_factory=list)
    skipped: list[Duplicate] = field(default_factory=list)


def _unversioned(name: str) -> str:
    # brew versions a formula as `python@3.14`; a leading `@` is an npm scope, not a version
    return name.split("@", 1)[0] if "@" in name[1:] else name


def dedupe(
    managers: Iterable[Manager],
    declared: set[str],
    replaced: Callable[[str], bool],
    yes: bool,
    aliases: Mapping[str, str] | None = None,
) -> Report:
    aliases = aliases or {}
    report = Report()
    for manager in managers:
        for name in sorted(manager.installed()):
            target = aliases.get(name) or _unversioned(name)
            if target not in declared or not replaced(target):
                continue
            found = Duplicate(manager.name, name)
            report.duplicates.append(found)
            if not yes:
                continue
            if manager.uninstall(name):
                report.removed.append(found)
            else:
                report.skipped.append(found)
    return report


class Runner(Protocol):
    def run(self, cmd: list[str], **kwargs: Any) -> Any: ...


@dataclass
class CommandManager:
    """A manager driven by one list command and one uninstall command per name."""

    ctx: Runner
    name: str
    list_cmd: list[str]
    parse: Callable[[str], set[str]]
    uninstall_cmd: Callable[[str], list[str]]

    @property
    def binary(self) -> str:
        return self.list_cmd[0]

    def installed(self) -> set[str]:
        result = self.ctx.run(
            self.list_cmd, capture_output=True, stream=False, echo=False, check=False
        )
        return self.parse(result.stdout) if result.returncode == 0 else set()

    def uninstall(self, name: str) -> bool:
        return self.ctx.run(self.uninstall_cmd(name), check=False).returncode == 0


def _lines(out: str) -> set[str]:
    return {line.strip() for line in out.splitlines() if line.strip()}


def _first_words(out: str) -> set[str]:
    return {line.split()[0] for line in out.splitlines() if line.split()}


def _npm_names(out: str) -> set[str]:
    return set(json.loads(out).get("dependencies", {})) if out.strip() else set()


def _cargo_names(out: str) -> set[str]:
    # crate lines start at column 0 ("name v1.2.3:"); their binaries are indented
    return {line.split()[0] for line in out.splitlines() if line[:1].strip()}


def brew_formulae(ctx: Runner) -> CommandManager:
    # `leaves` skips dependencies, so a formula another one needs is never offered
    return CommandManager(
        ctx,
        "brew",
        ["brew", "leaves"],
        _lines,
        lambda n: ["brew", "uninstall", "--formula", n],
    )


def brew_casks(ctx: Runner) -> CommandManager:
    return CommandManager(
        ctx,
        "brew cask",
        ["brew", "list", "--cask", "-1"],
        _lines,
        lambda n: ["brew", "uninstall", "--cask", n],
    )


def npm_global(ctx: Runner) -> CommandManager:
    return CommandManager(
        ctx,
        "npm",
        ["npm", "ls", "-g", "--depth=0", "--json"],
        _npm_names,
        lambda n: ["npm", "uninstall", "-g", n],
    )


def pipx_global(ctx: Runner) -> CommandManager:
    return CommandManager(
        ctx,
        "pipx",
        ["pipx", "list", "--short"],
        _first_words,
        lambda n: ["pipx", "uninstall", n],
    )


def cargo_global(ctx: Runner) -> CommandManager:
    return CommandManager(
        ctx,
        "cargo",
        ["cargo", "install", "--list"],
        _cargo_names,
        lambda n: ["cargo", "uninstall", n],
    )


@dataclass
class GoManager:
    """Go has no uninstall command: a `go install` is a binary in GOBIN or GOPATH/bin."""

    ctx: Runner
    name: str = "go"
    binary: str = "go"

    def _bin_dir(self) -> Path | None:
        result = self.ctx.run(
            ["go", "env", "GOBIN", "GOPATH"],
            capture_output=True,
            stream=False,
            echo=False,
            check=False,
        )
        if result.returncode != 0:
            return None
        gobin, gopath, *_ = [*result.stdout.split("\n"), ""]
        if gobin.strip():
            return Path(gobin.strip())
        first = gopath.strip().split(os.pathsep)[0]
        return Path(first) / "bin" if first else None

    def installed(self) -> set[str]:
        bin_dir = self._bin_dir()
        if bin_dir is None or not bin_dir.is_dir():
            return set()
        return {p.name for p in bin_dir.iterdir() if _is_plain_file(p)}

    def uninstall(self, name: str) -> bool:
        bin_dir = self._bin_dir()
        target = bin_dir / name if bin_dir else None
        if target is None or not _is_plain_file(target):
            return False
        target.unlink()
        return True


def _is_plain_file(path: Path) -> bool:
    # a symlink in a shared bin dir is someone else's script, never a `go install`
    return path.is_file() and not path.is_symlink()


def go_global(ctx: Runner) -> GoManager:
    return GoManager(ctx)


def _tool_name(key: str) -> str:
    # "pipx:bakefile" -> "bakefile"; "go:golang.org/x/tools/gopls" -> "gopls"; npm keeps its scope
    backend, _, rest = key.partition(":")
    if not rest:
        return key
    return rest if backend == "npm" else rest.rsplit("/", 1)[-1]


def declared_mise_tools(root: Path) -> dict[str, str]:
    """Comparable name -> the full mise key, which `mise where` needs."""
    names: dict[str, str] = {}
    for filename in ("mise.toml", "mise.private.toml"):
        path = root / filename
        if path.is_file():
            tools = tomllib.loads(path.read_text()).get("tools", {})
            names |= {_tool_name(key): key for key in tools}
    return names


CASK = re.compile(r"""^\s*cask\s+["']([^"']+)["']""")


def declared_casks(brewfiles: Iterable[Path]) -> set[str]:
    return {
        match.group(1)
        for brewfile in brewfiles
        for line in brewfile.read_text().splitlines()
        if (match := CASK.match(line))
    }


# Names that differ between a package manager and mise; extend when dedupe misses one
ALIASES: Mapping[str, str] = {
    "python@3.13": "python",
    "openjdk": "java",
    "google-cloud-sdk": "gcloud",
    "gcloud-cli": "gcloud",
}
