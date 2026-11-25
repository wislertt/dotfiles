import os
import shutil
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer
from bake import command, console
from bakelib.space import BaseSpace

from src.python.core import brewfiles, repo, signing
from src.python.core import tidy as core
from src.python.core.tidy import Stray

APPLICATIONS = Path("/Applications")
IS_MACOS = sys.platform == "darwin"
# System directories are read-only even to sudo, so nothing in them is reported
SYSTEM_BIN_DIRS = ("/usr/bin", "/bin", "/usr/sbin", "/sbin")


class TidyMixin(BaseSpace):
    if TYPE_CHECKING:
        # MachineMixin provides it in the bakebook
        def _roles(self) -> list[str]: ...

    @command(
        help="Remove every Stray bake can remove and list the rest with the command to run"
    )
    def tidy(
        self,
        check: Annotated[
            bool, typer.Option(help="List only, remove nothing; fail if any Stray")
        ] = False,
        caches: Annotated[
            bool,
            typer.Option(help="Also clear Docker and Mole caches (not with --check)"),
        ] = False,
        volumes: Annotated[
            bool, typer.Option(help="With --caches, also remove unused Docker volumes")
        ] = False,
    ) -> None:
        if volumes and not caches:
            console.error("--volumes needs --caches")
            raise SystemExit(1)
        roles = self._roles()
        keep = core.keep_list(repo.ROOT, roles)
        strays = [s for s in self._strays(roles) if s.key not in keep]
        if check:
            for line in core.check_report(strays):
                console.echo(line)
            if strays:
                raise SystemExit(1)
            return
        removed = failed = left = 0
        brew_uninstalled = False
        for label, kinds, tool in core.SOURCES:
            if kinds == ("app",) and not IS_MACOS:
                continue
            if tool and not shutil.which(tool):
                if tool not in core.QUIET_WHEN_MISSING:
                    console.info(f"{label}: skipped, {tool} is not installed")
                continue
            here = [s for s in strays if s.kind in kinds]
            need_you = sum(1 for s in here if not s.remove)
            for stray in (s for s in here if s.remove):
                if self._remove(stray):
                    console.success(f"Removed {stray.key}")
                    removed += 1
                    brew_uninstalled |= stray.kind in ("brew", "cask")
                else:
                    console.warning(f"Could not remove {stray.key}")
                    failed += 1
                    need_you += 1
            if need_you:
                console.info(f"{label}: {need_you} need you")
            else:
                console.success(f"{label}: clean")
            left += need_you
        # an uninstall can leave dependencies nothing needs any more
        if brew_uninstalled:
            self.ctx.run(["brew", "autoremove"])
        caches_failed = self._clear_caches(volumes) if caches else 0
        summary = [f"Removed {removed}"]
        if failed:
            summary.append(f"{failed} could not be removed")
        summary.append(
            f"{left} need you: run `bake tidy --check`" if left else "Nothing needs you"
        )
        console.echo(". ".join(summary))
        if failed or caches_failed:
            raise SystemExit(1)

    def _clear_caches(self, volumes: bool) -> int:
        """Returns how many cleaners failed."""
        failed = 0
        for label, tool, cmd in core.cache_cleaners(volumes, IS_MACOS):
            if not shutil.which(tool):
                console.info(f"{label}: skipped, {tool} is not installed")
            elif tool == "docker" and self._manager_output("docker", "info") is None:
                console.info(f"{label}: skipped, Docker is not running")
            elif self.ctx.run(list(cmd), check=False).returncode == 0:
                console.success(f"{label}: caches cleared")
            else:
                console.warning(f"{label}: could not clear caches")
                failed += 1
        return failed

    def _remove(self, stray: Stray) -> bool:
        """Runs the commands in order and stops at the first that fails."""
        return all(
            self.ctx.run(list(cmd), check=False).returncode == 0 for cmd in stray.remove
        )

    def _manager_output(self, *cmd: str, ok: tuple[int, ...] = (0,)) -> str | None:
        """None when the manager is not installed or fails."""
        if not shutil.which(cmd[0]):
            return None
        result = self.ctx.run(
            list(cmd), capture_output=True, stream=False, echo=False, check=False
        )
        return result.stdout if result.returncode in ok else None

    def _strays(self, roles: list[str]) -> list[Stray]:
        path = [Path(p) for p in os.environ.get("PATH", "").split(os.pathsep) if p]
        return [
            *self._brew_strays(roles),
            *self._manager_strays(),
            *core.filesystem_strays(path, Path.home(), map(Path, SYSTEM_BIN_DIRS)),
            *self._app_strays(),
            *self._signing_key_strays(),
            *self._ssh_key_strays(),
            *self._rust_toolchain_strays(),
            *core.duplicate_strays(self._copies(path), Path.home()),
        ]

    def _app_strays(self) -> list[Stray]:
        if not IS_MACOS:
            return []
        info = (
            self._manager_output("brew", "info", "--cask", "--installed", "--json=v2")
            or ""
        )
        owned = core.apps_owned_by_casks(info)
        # a pkg cask names its receipts, not the apps they install
        for pattern in core.cask_receipt_patterns(info):
            ids = self._manager_output("pkgutil", f"--pkgs={pattern}") or ""
            for pkg in ids.split():
                files = self._manager_output("pkgutil", "--files", pkg) or ""
                owned |= core.receipt_apps(files)
        return core.app_strays(APPLICATIONS, owned)

    def _signing_key_strays(self) -> list[Stray]:
        if not shutil.which("gh"):
            return []
        key = signing.SigningKey.for_this_machine(self.ctx)
        found = key.github_keys()
        if found is None:
            return []
        return core.signing_key_strays(found, key.local_key_id(), key.now())

    def _ssh_key_strays(self) -> list[Stray]:
        if not shutil.which("gh"):
            return []
        result = self.ctx.run(
            ["gh", "api", "--paginate", "--slurp", "user/keys"],
            # the stored gh login, and no colour in the JSON (bake runs it in a pty)
            env={**dict.fromkeys(signing.GH_TOKEN_VARS), "NO_COLOR": "1"},
            capture_output=True,
            stream=False,
            echo=False,
            check=False,
        )
        if result.returncode:
            console.warning(
                "GitHub SSH keys: not checked, gh needs the read:public_key scope:"
                " run `gh auth refresh -h github.com -s read:public_key`"
            )
            return []
        return core.ssh_key_strays(result.stdout)

    def _rust_toolchain_strays(self) -> list[Stray]:
        listing = self._manager_output("rustup", "toolchain", "list")
        if not listing:
            return []
        pins = core.rust_pins(core.repos_roots(repo.ROOT))
        return core.rust_toolchain_strays(listing, pins)

    def _copies(self, path: list[Path]) -> list[core.Copy]:
        tool_bins: dict[str, list[Path]] = {}
        for key in sorted(core.declared_mise_tools(repo.ROOT)):
            out = self._manager_output("mise", "bin-paths", key)
            # not installed yet: nothing to be a duplicate of
            if out and out.strip():
                tool_bins[key] = [Path(p) for p in out.split()]
        ignore = [
            *map(Path, SYSTEM_BIN_DIRS),
            # mise shims and project virtualenvs are not installs
            *(p for p in path if p.parts[-2:] in (("mise", "shims"), (".venv", "bin"))),
        ]
        return core.other_copies(tool_bins, path, ignore)

    def _brew_strays(self, roles: list[str]) -> list[Stray]:
        found = brewfiles.paths(repo.ROOT, roles)
        if not found:
            return []
        # each listing counts the other Brewfile's apps as undeclared, so a Stray is in every listing
        listings = [
            core.cleanup_listing(
                self._manager_output(
                    "brew", "bundle", "cleanup", "--file", str(f), ok=(0, 1)
                )
                or ""
            )
            for f in found
        ]

        def in_all(kind: str) -> list[str]:
            return [n for n in listings[0][kind] if all(n in l[kind] for l in listings)]

        # a formula something depends on goes with brew autoremove instead
        leaves = set((self._manager_output("brew", "leaves") or "").split())
        return [
            *(
                Stray("brew", name, remove=(("brew", "uninstall", name),))
                for name in in_all("formulae")
                if name in leaves
            ),
            *(
                Stray("cask", name, remove=(("brew", "uninstall", "--cask", name),))
                for name in in_all("casks")
            ),
        ]

    def _manager_strays(self) -> list[Stray]:
        managers = (
            ("uv", ("uv", "tool", "list"), core.uv_tools, ("uv", "tool", "uninstall")),
            (
                "cargo",
                ("cargo", "install", "--list"),
                core.cargo_crates,
                ("cargo", "uninstall"),
            ),
            (
                "npm",
                ("npm", "ls", "-g", "--depth=0", "--json"),
                core.npm_globals,
                ("npm", "uninstall", "-g"),
            ),
            (
                "pnpm",
                ("pnpm", "ls", "-g", "--json"),
                core.pnpm_globals,
                ("pnpm", "remove", "-g"),
            ),
        )
        return [
            Stray(kind, name, remove=((*uninstall, name),))
            for kind, listing, parse, uninstall in managers
            if (out := self._manager_output(*listing)) is not None
            for name in parse(out)
        ]
