# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "bakefile[lib]>=0.0.84",
# ]
# ///

from collections.abc import Mapping
from typing import ClassVar, cast

from bakelib.refreshable_cache import FetchFn, FnoxFetchFn
from bakelib.space import FnoxSpace, SubmodulesUtils

# Names the scripts in src/bin read with `bake secret get`; the references live in fnox.toml
SECRET_KEYS = ("CLAUDE_GLM_AUTH_TOKEN",)


class MyBakebook(SubmodulesUtils, FnoxSpace[str | None]):
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

    def test(self) -> None:
        # assert-setup-dev calls test(); a dotfiles repo has nothing to test
        pass


bakebook = MyBakebook()
