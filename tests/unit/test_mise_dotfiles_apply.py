from pathlib import Path

import pytest

import bakefile
from tests.unit.conftest import FakeCtx


def test_public_clone_applies_without_the_private_environment(
    bakebook: bakefile.MyBakebook, fake_ctx: FakeCtx, fake_repo: Path
) -> None:
    del fake_repo
    bakebook._run_mise_dotfiles_apply()
    assert fake_ctx.commands == [["mise", "dotfiles", "apply"]]


def test_private_companion_adds_the_private_environment(
    bakebook: bakefile.MyBakebook, fake_ctx: FakeCtx, fake_repo: Path
) -> None:
    (fake_repo / "private" / "src").mkdir(parents=True)
    bakebook._run_mise_dotfiles_apply()
    assert fake_ctx.commands == [["mise", "-E", "private", "dotfiles", "apply"]]


@pytest.mark.parametrize("flag", ["--force", "-f", "--yes", "-y"])
def test_apply_never_forces_or_skips_confirmation(
    bakebook: bakefile.MyBakebook, fake_ctx: FakeCtx, fake_repo: Path, flag: str
) -> None:
    (fake_repo / "private" / "src").mkdir(parents=True)
    bakebook._run_mise_dotfiles_apply()
    assert all(flag not in cmd for cmd in fake_ctx.commands)


def test_failed_mise_apply_exits_nonzero(
    bakebook: bakefile.MyBakebook, fake_ctx: FakeCtx, fake_repo: Path
) -> None:
    del fake_repo
    fake_ctx.returncode = 1
    with pytest.raises(SystemExit) as exc:
        bakebook._run_mise_dotfiles_apply()
    assert exc.value.code == 1
