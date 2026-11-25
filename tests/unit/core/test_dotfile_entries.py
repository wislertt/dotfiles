from pathlib import Path

from src.python.core import dotfile_entries


def test_an_fnox_entry_writes_a_secret(tmp_path: Path) -> None:
    (tmp_path / "mise.toml").write_text(
        '[dotfiles."~/.netrc"]\nmode = "fnox"\nsource = "src/lib/netrc"\n'
    )
    assert dotfile_entries.secret_writers(tmp_path) == ["mise.toml: ~/.netrc"]


def test_a_template_that_calls_secret_writes_a_secret(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "npmrc").write_text('token={{ secret(name="NPM") }}\n')
    (tmp_path / "src" / "gitconfig").write_text("name={{ env.USER }}\n")
    (tmp_path / "mise.private.toml").write_text(
        '[dotfiles."~/.npmrc"]\nmode = "template"\nsource = "src/npmrc"\n'
        '[dotfiles."~/.gitconfig"]\nmode = "template"\nsource = "src/gitconfig"\n'
    )
    assert dotfile_entries.secret_writers(tmp_path) == ["mise.private.toml: ~/.npmrc"]


def test_links_and_merges_write_no_secret(tmp_path: Path) -> None:
    (tmp_path / "mise.toml").write_text(
        '[dotfiles."~/.config/bake"]\nmode = "symlink"\nsource = "."\n'
        '[dotfiles."~/.claude/settings.json/enforced"]\nsource = "a.json"\nmerge = true\n'
    )
    assert dotfile_entries.secret_writers(tmp_path) == []
