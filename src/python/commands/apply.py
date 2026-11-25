from unittest.mock import patch

from bake import command, console
from bakelib.refreshable_cache.fnox import run_fnox
from bakelib.space import FnoxSpace
from bakelib.space import fnox as fnox_space

from src.python.commands.secrets import SECRET_KEYS
from src.python.core import repo


class ApplyMixin(FnoxSpace[str | None]):
    @command()
    def apply(self) -> None:
        """Link dotfiles into ~ with mise (never overwrites a regular file), then assert use-time needs"""
        self._apply()

    def _apply(self) -> None:
        self._run_mise_dotfiles_apply()
        self._assert_dotfiles_readiness()

    def _run_mise_dotfiles_apply(self) -> None:
        # No --force and no --yes: a conflicting regular file makes mise exit non-zero
        cmd = ["mise", "dotfiles", "apply"]
        if (repo.ROOT / "private" / "src").is_dir():
            cmd[1:1] = ["-E", "private"]
        if self.ctx.run(cmd, check=False).returncode != 0:
            console.error(
                "Apply failed. If the output above names files that already exist and are not managed, "
                "move or delete each one, then rerun `bake apply`. "
                "To overwrite on purpose, run `mise dotfiles apply --force` yourself (not via bake)."
            )
            raise SystemExit(1)

    def _assert_dotfiles_readiness(self) -> None:
        # Read-only: reports names only, never values, and writes nothing
        failures = self._bakelib_assert_failures()
        if not failures:
            failures = self._unresolved_secret_failures()
        if failures:
            for failure in failures:
                console.error(failure)
            console.error("Assert failed")
            raise SystemExit(1)
        console.success("Assert passed")

    def _bakelib_assert_failures(self) -> list[str]:
        # bakelib's asserts only print, so collect what they report
        failures: list[str] = []
        with (
            patch.object(fnox_space.console, "error", side_effect=failures.append),
            patch.object(fnox_space.console, "cmd"),
        ):
            self._assert_age_key()
            self._assert_bootstrap_secrets()
        return failures

    def _unresolved_secret_failures(self) -> list[str]:
        return [
            f"secret {key} does not resolve"
            for key in SECRET_KEYS
            if not self._secret_resolves(key)
        ]

    def _secret_resolves(self, key: str) -> bool:
        if self.vault().has_value(key):
            return True
        # not cached yet (fresh Mac): ask fnox directly, which does not write the cache
        return run_fnox(["--no-daemon", "get", key]).returncode == 0
