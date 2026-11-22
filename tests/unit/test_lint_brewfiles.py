from pathlib import Path

import pytest

import bakefile
from tests.unit.conftest import FakeCtx


def test_a_cask_only_brewfile_passes(
    bakebook: bakefile.MyBakebook, fake_ctx: FakeCtx, fake_repo: Path
) -> None:
    (fake_repo / "src" / "lib" / "Brewfile").write_text(
        "# apps\n\ncask \"zed\"\ncask 'docker-desktop'\n"
    )
    bakebook._lint_brewfiles()


@pytest.mark.parametrize(
    "line", ['brew "jq"', 'tap "x/y"', 'mas "X", id: 1', "cask zed"]
)
def test_a_brewfile_with_anything_but_casks_fails_and_is_named(
    bakebook: bakefile.MyBakebook, fake_repo: Path, line: str
) -> None:
    (fake_repo / "src" / "lib" / "Brewfile").write_text(f'cask "zed"\n{line}\n')
    with pytest.raises(SystemExit) as exc:
        bakebook._lint_brewfiles()
    assert "Brewfile" in str(exc.value)


def test_the_private_brewfile_is_linted_too(
    bakebook: bakefile.MyBakebook, fake_repo: Path
) -> None:
    (fake_repo / "private" / "src" / "lib").mkdir(parents=True)
    (fake_repo / "private" / "src" / "lib" / "Brewfile").write_text('brew "jq"\n')
    with pytest.raises(SystemExit):
        bakebook._lint_brewfiles()


def test_brew_parses_each_brewfile_when_available(
    bakebook: bakefile.MyBakebook,
    fake_ctx: FakeCtx,
    fake_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (fake_repo / "src" / "lib" / "Brewfile").write_text('cask "zed"\n')
    monkeypatch.setattr(
        bakefile.shutil, "which", lambda _name: "/opt/homebrew/bin/brew"
    )
    bakebook._lint_brewfiles()
    assert [c[:3] for c in fake_ctx.commands] == [["brew", "bundle", "list"]]


def test_no_brew_parse_without_brew(
    bakebook: bakefile.MyBakebook,
    fake_ctx: FakeCtx,
    fake_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (fake_repo / "src" / "lib" / "Brewfile").write_text('cask "zed"\n')
    monkeypatch.setattr(bakefile.shutil, "which", lambda _name: None)
    bakebook._lint_brewfiles()
    assert fake_ctx.commands == []
