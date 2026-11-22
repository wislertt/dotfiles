import pytest

from src.python import bakefile
from tests.unit.conftest import FakeCtx, FakeVault

TOKEN = "FNOX_BWS_ACCESS_TOKEN"


@pytest.fixture(autouse=True)
def no_terminal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("bakelib.space.fnox.can_prompt", lambda: False)


def test_token_in_env_is_stored_without_a_terminal(
    bakebook: bakefile.MyBakebook,
    fake_vault: FakeVault,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(TOKEN, "dummy-token")
    bakebook._ensure_bootstrap_secrets()
    assert fake_vault.stored == {TOKEN: "dummy-token"}


def test_no_token_in_env_stores_nothing(
    bakebook: bakefile.MyBakebook,
    fake_vault: FakeVault,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(TOKEN, raising=False)
    bakebook._ensure_bootstrap_secrets()
    assert fake_vault.stored == {}


def test_a_cached_token_is_not_overwritten_by_env(
    bakebook: bakefile.MyBakebook,
    fake_vault: FakeVault,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_vault.values.add(TOKEN)
    monkeypatch.setenv(TOKEN, "other")
    bakebook._ensure_bootstrap_secrets()
    assert fake_vault.stored == {}


def test_dry_run_stores_nothing(
    bakebook: bakefile.MyBakebook,
    fake_ctx: FakeCtx,
    fake_vault: FakeVault,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_ctx.dry_run = True
    monkeypatch.setenv(TOKEN, "dummy-token")
    bakebook._ensure_bootstrap_secrets()
    assert fake_vault.stored == {}
