from pathlib import Path

import pytest

from src.python import bakefile


def test_lint_fails_on_a_dotfile_entry_that_writes_a_secret(
    bakebook: bakefile.MyBakebook, fake_repo: Path
) -> None:
    (fake_repo / "mise.toml").write_text('[dotfiles."~/.netrc"]\nmode = "fnox"\n')
    with pytest.raises(SystemExit, match=r"~/\.netrc"):
        bakebook._lint_secret_writers()


def test_lint_passes_when_no_entry_writes_a_secret(
    bakebook: bakefile.MyBakebook, fake_repo: Path
) -> None:
    (fake_repo / "mise.toml").write_text('[dotfiles."~/.config/bake"]\nsource = "."\n')
    bakebook._lint_secret_writers()
