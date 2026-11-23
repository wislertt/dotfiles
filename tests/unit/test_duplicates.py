import os
from pathlib import Path

import pytest

from src.python.duplicates import Copy, declared_mise_tools, other_copies


def _exe(directory: Path, *names: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    for name in names:
        path = directory / name
        path.write_text("")
        path.chmod(0o755)
    return directory


def test_a_copy_earlier_or_later_on_path_is_reported(tmp_path: Path) -> None:
    mise = _exe(tmp_path / "mise" / "jq", "jq")
    brew = _exe(tmp_path / "brew", "jq", "other")
    found = other_copies({"jq": [mise]}, path=[mise, brew], ignore=[])
    assert found == [Copy("jq", "jq", brew / "jq")]


def test_the_tools_own_directory_is_not_a_duplicate(tmp_path: Path) -> None:
    mise = _exe(tmp_path / "jq", "jq")
    assert other_copies({"jq": [mise]}, path=[mise], ignore=[]) == []


def test_an_unrelated_binary_with_another_name_is_not_reported(tmp_path: Path) -> None:
    mise = _exe(tmp_path / "mise" / "uv", "uv", "uvx")
    brew = _exe(tmp_path / "brew", "ripgrep")
    assert other_copies({"uv": [mise]}, path=[mise, brew], ignore=[]) == []


def test_every_binary_the_tool_ships_is_checked(tmp_path: Path) -> None:
    mise = _exe(tmp_path / "mise" / "uv", "uv", "uvx")
    brew = _exe(tmp_path / "brew", "uvx")
    found = other_copies({"uv": [mise]}, path=[mise, brew], ignore=[])
    assert found == [Copy("uv", "uvx", brew / "uvx")]


def test_ignored_directories_such_as_system_bins_and_shims_are_skipped(
    tmp_path: Path,
) -> None:
    mise = _exe(tmp_path / "mise" / "jq", "jq")
    system = _exe(tmp_path / "usr-bin", "jq")
    assert other_copies({"jq": [mise]}, path=[mise, system], ignore=[system]) == []


def test_a_non_executable_file_is_not_a_copy(tmp_path: Path) -> None:
    mise = _exe(tmp_path / "mise" / "shellcheck", "shellcheck")
    notes = tmp_path / "brew"
    notes.mkdir()
    (notes / "shellcheck").write_text("")  # no execute bit
    assert other_copies({"shellcheck": [mise]}, path=[mise, notes], ignore=[]) == []


def test_a_copy_on_path_twice_is_reported_once(tmp_path: Path) -> None:
    mise = _exe(tmp_path / "mise" / "jq", "jq")
    brew = _exe(tmp_path / "brew", "jq")
    found = other_copies({"jq": [mise]}, path=[mise, brew, brew], ignore=[])
    assert len(found) == 1


def test_declared_mise_tools_are_the_keys_of_both_files(tmp_path: Path) -> None:
    (tmp_path / "mise.toml").write_text(
        '[tools]\njq = "latest"\n"npm:oxfmt" = "latest"\n'
        '"pipx:bakefile" = { version = "latest", extras = "locked" }\n'
    )
    (tmp_path / "mise.private.toml").write_text('[tools]\n"cargo:zerv" = "latest"\n')
    assert declared_mise_tools(tmp_path) == {
        "jq",
        "npm:oxfmt",
        "pipx:bakefile",
        "cargo:zerv",
    }


def test_declared_mise_tools_without_a_tools_table_or_private_file(
    tmp_path: Path,
) -> None:
    (tmp_path / "mise.toml").write_text("[bootstrap]\ndotfile_groups = []\n")
    assert declared_mise_tools(tmp_path) == set()


@pytest.mark.skipif(os.name == "nt", reason="execute bits")
def test_symlinks_to_other_installs_count_as_copies(tmp_path: Path) -> None:
    mise = _exe(tmp_path / "mise" / "jq", "jq")
    cellar = _exe(tmp_path / "cellar", "jq")
    brew = tmp_path / "brew"
    brew.mkdir()
    (brew / "jq").symlink_to(cellar / "jq")
    assert other_copies({"jq": [mise]}, path=[mise, brew], ignore=[]) == [
        Copy("jq", "jq", brew / "jq")
    ]
