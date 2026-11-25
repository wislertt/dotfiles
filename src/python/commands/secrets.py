from collections.abc import Mapping
from typing import ClassVar, cast

from bakelib.refreshable_cache import FetchFn, FnoxFetchFn
from bakelib.space import FnoxSpace

# Names the scripts in src/bin read with `bake secret get`; the references live in fnox.toml
SECRET_KEYS = ("CLAUDE_GLM_AUTH_TOKEN", "AICLIENT2API_API_KEY")


class SecretsMixin(FnoxSpace[str | None]):
    fnox_bootstrap_secrets: ClassVar[Mapping[str, str]] = {
        "FNOX_BWS_ACCESS_TOKEN": "Bitwarden access token",
    }

    def get_secret_fetch_fns(self) -> tuple[FetchFn[str | None], ...]:
        return (
            *super().get_secret_fetch_fns(),
            *(cast("FetchFn[str | None]", FnoxFetchFn(key)) for key in SECRET_KEYS),
        )
