from collections.abc import Mapping
from pathlib import Path
from typing import ClassVar, cast

from bake import command
from bakelib.refreshable_cache import FetchFn, FnoxFetchFn
from bakelib.space import FnoxSpace, PythonSpace, SubmodulesUtils
from bakelib.space.params import DurationsOption

# Names the scripts in src/bin read with `bake secret get`; the references live in fnox.toml
SECRET_KEYS = ("CLAUDE_GLM_AUTH_TOKEN",)


class MyBakebook(SubmodulesUtils, FnoxSpace[str | None], PythonSpace):
    fnox_bootstrap_secrets: ClassVar[Mapping[str, str]] = {
        "FNOX_BWS_ACCESS_TOKEN": "Bitwarden access token",
    }

    def get_secret_fetch_fns(self) -> tuple[FetchFn[str | None], ...]:
        return (
            *super().get_secret_fetch_fns(),
            *(cast("FetchFn[str | None]", FnoxFetchFn(key)) for key in SECRET_KEYS),
        )

    __exclude_command_methods__: ClassVar[list[str]] = [
        "test",
        "test_all",
        "test_integration",
    ]

    def _lint_fast(self) -> None:
        super()._lint_fast()
        self._assert_global_fnox_empty()

    def _assert_global_fnox_empty(self) -> None:
        # Secrets come only from `bake secret get`; the global fnox config must stay unused
        path = Path.home() / ".config" / "fnox" / "config.toml"
        if not path.exists():
            return
        # fnox exits 0 either way, so judge by output
        secrets = self._fnox_out("list", "-c", str(path))
        providers = self._fnox_out("provider", "list", "-c", str(path))
        if providers or not secrets.startswith("No secrets defined"):
            raise SystemExit(f"Global fnox config is not empty: {path}. Clear it.")

    def _fnox_out(self, *args: str) -> str:
        cmd = ["fnox", "--no-color", "--no-daemon", *args]
        return self.ctx.run(
            cmd, capture_output=True, stream=False, echo=False
        ).stdout.strip()

    @command()
    def apply(self) -> None:
        """Link dotfiles into ~ with mise (overwrites existing files)"""
        self.ctx.run("mise dotfiles apply --force")

    def test(self, durations: DurationsOption = None) -> None:
        # assert-setup-dev calls test(); a dotfiles repo has nothing to test
        del durations


bakebook = MyBakebook()
