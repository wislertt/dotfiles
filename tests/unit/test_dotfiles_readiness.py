from pathlib import Path
from types import SimpleNamespace

import pytest

import bakefile
from tests.unit.conftest import FakeVault


@pytest.fixture
def set_up_machine(
    bakebook: bakefile.MyBakebook, fake_vault: FakeVault, tmp_path: Path
) -> bakefile.MyBakebook:
    """Age key present and the bootstrap token stored; secrets resolve unless a test says not."""
    key = tmp_path / "age.txt"
    key.write_text("key")
    bakebook.fnox_age_key_file = key
    fake_vault.values.update(bakefile.MyBakebook.fnox_bootstrap_secrets)
    return bakebook


@pytest.fixture
def fnox_returncode(monkeypatch: pytest.MonkeyPatch) -> dict[str, int]:
    """What `fnox get` answers for a secret that is not cached; keyed per run, default success."""
    answer = {"code": 0}
    monkeypatch.setattr(
        bakefile, "run_fnox", lambda _args: SimpleNamespace(returncode=answer["code"])
    )
    return answer


def test_missing_age_key_fails_the_assert(
    bakebook: bakefile.MyBakebook, tmp_path: Path
) -> None:
    bakebook.fnox_age_key_file = tmp_path / "no-age-key.txt"
    with pytest.raises(SystemExit) as exc:
        bakebook._assert_dotfiles_readiness()
    assert exc.value.code == 1


def test_unresolved_secret_fails_the_assert(
    set_up_machine: bakefile.MyBakebook,
    fnox_returncode: dict[str, int],
    capsys: pytest.CaptureFixture[str],
) -> None:
    fnox_returncode["code"] = 1
    with pytest.raises(SystemExit) as exc:
        set_up_machine._assert_dotfiles_readiness()
    assert exc.value.code == 1
    assert bakefile.SECRET_KEYS[0] in capsys.readouterr().err


def test_ready_machine_passes_the_assert(
    set_up_machine: bakefile.MyBakebook, fnox_returncode: dict[str, int]
) -> None:
    del fnox_returncode
    set_up_machine._assert_dotfiles_readiness()
