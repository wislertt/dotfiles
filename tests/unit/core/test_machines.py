from pathlib import Path

import pytest

from src.python.core import machines

IOREG = """+-o J516sAP  <class IOPlatformExpertDevice>
    {
      "IOPlatformUUID" = "0000"
      "IOPlatformSerialNumber" = "SERIAL0001"
      "model" = <"Mac15,7">
    }
"""


def test_the_serial_is_read_from_ioreg() -> None:
    assert machines.serial(IOREG) == "SERIAL0001"


def test_no_serial_when_ioreg_says_nothing() -> None:
    assert machines.serial("") is None


def _machines(root: Path, text: str) -> None:
    path = root / "private" / "src" / "lib" / "machines.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def test_a_listed_machine_has_its_name_and_roles(tmp_path: Path) -> None:
    _machines(
        tmp_path,
        '"SERIAL0001" = { name = "work-mac", roles = ["work", "studio"] }\n'
        '"OTHER" = { name = "home-mac", roles = ["home"] }\n',
    )
    assert machines.roles(tmp_path, "SERIAL0001") == ["work", "studio"]
    assert machines.name(tmp_path, "SERIAL0001") == "work-mac"


def test_roles_are_optional(tmp_path: Path) -> None:
    _machines(tmp_path, '"SERIAL0001" = { name = "work-mac" }\n')
    assert machines.roles(tmp_path, "SERIAL0001") == []


@pytest.mark.parametrize("serial", ["UNLISTED", None])
def test_an_unknown_machine_has_no_name_or_roles(
    tmp_path: Path, serial: str | None
) -> None:
    _machines(tmp_path, '"SERIAL0001" = { name = "work-mac", roles = ["work"] }\n')
    assert machines.roles(tmp_path, serial) == []
    assert machines.name(tmp_path, serial) is None


def test_no_machine_list_means_no_name_or_roles(tmp_path: Path) -> None:
    assert machines.roles(tmp_path, "SERIAL0001") == []
    assert machines.name(tmp_path, "SERIAL0001") is None


@pytest.mark.parametrize(
    "text",
    [
        '"S" = ["work"]\n',
        '"S" = { roles = ["work"] }\n',
        '"S" = { name = "Work Mac" }\n',
        '"S" = { name = "m", roles = "work" }\n',
        '"S" = { name = "m", roles = ["../x"] }\n',
        '"S" = { name = "m", role = ["work"] }\n',
    ],
)
def test_a_malformed_machine_list_fails_clearly(tmp_path: Path, text: str) -> None:
    _machines(tmp_path, text)
    with pytest.raises(SystemExit, match="machines.toml"):
        machines.roles(tmp_path, "S")


def test_adding_a_machine_appends_it_and_keeps_the_rest(tmp_path: Path) -> None:
    _machines(tmp_path, '# header\n"OTHER" = { name = "home-mac", roles = ["home"] }')
    machines.add(tmp_path, "SERIAL0001", "work-mac")
    assert machines.name(tmp_path, "SERIAL0001") == "work-mac"
    assert machines.roles(tmp_path, "OTHER") == ["home"]
    assert machines.path(tmp_path).read_text().startswith("# header\n")


def test_adding_creates_the_list_in_the_private_repo(tmp_path: Path) -> None:
    (tmp_path / "private" / "src" / "lib").mkdir(parents=True)
    machines.add(tmp_path, "SERIAL0001", "work-mac")
    assert machines.name(tmp_path, "SERIAL0001") == "work-mac"


def test_adding_without_the_private_repo_fails(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="nowhere to save"):
        machines.add(tmp_path, "SERIAL0001", "work-mac")


@pytest.mark.parametrize(
    ("machine_id", "new", "error"),
    [
        ("SERIAL0001", "Work Mac", "lowercase"),
        ("SERIAL0001", "home-mac", "another machine"),
        ("OTHER", "work-mac", "already named"),
    ],
)
def test_adding_rejects_a_bad_or_taken_name(
    tmp_path: Path, machine_id: str, new: str, error: str
) -> None:
    _machines(tmp_path, '"OTHER" = { name = "home-mac" }\n')
    with pytest.raises(ValueError, match=error):
        machines.add(tmp_path, machine_id, new)


def test_the_linux_id_is_the_first_non_empty_file(tmp_path: Path) -> None:
    empty, full = tmp_path / "a", tmp_path / "b"
    empty.write_text("\n")
    full.write_text("abc123\n")
    assert machines.linux_id([tmp_path / "missing", empty, full]) == "abc123"
    assert machines.linux_id([empty]) is None
