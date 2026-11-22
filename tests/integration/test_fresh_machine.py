from pathlib import Path

from tests.integration.conftest import Machine


def test_public_clone_applies_and_a_second_apply_changes_nothing(
    public_machine: Machine,
) -> None:
    first = public_machine.apply()
    assert first.returncode == 0, first.stderr
    links = public_machine.links()
    assert links
    assert all((public_machine.home / rel).exists() for rel in links)

    second = public_machine.apply()
    assert second.returncode == 0, second.stderr
    assert public_machine.links() == links


def test_existing_regular_file_is_refused_named_and_left_untouched(
    public_machine: Machine,
) -> None:
    target = Path(".zshenv")
    (public_machine.home / target).write_text("keep")

    result = public_machine.apply()

    assert result.returncode != 0
    assert str(target) in result.stderr
    assert (public_machine.home / target).read_text() == "keep"
    assert not (public_machine.home / target).is_symlink()


def test_private_groups_load_when_the_private_companion_is_present(
    private_machine: Machine,
) -> None:
    result = private_machine.apply("-E", "private")
    assert result.returncode == 0, result.stderr

    links = private_machine.links()
    for source in (private_machine.repo / "private" / "src").rglob("*"):
        if not source.is_file():
            continue
        group, _, rest = (
            source.relative_to(private_machine.repo / "private" / "src")
            .as_posix()
            .partition("/")
        )
        if group == "lib":  # read from the repo, never linked
            assert source not in links.values()
            continue
        base = {"bin": Path(".local/bin"), "config": Path(".config"), "home": Path()}[
            group
        ]
        assert links[base / rest] == source


def test_two_groups_claiming_one_target_are_rejected(private_machine: Machine) -> None:
    clash = private_machine.repo / "private" / "src" / "home" / ".zshenv"
    clash.write_text("clash")

    result = private_machine.apply("-E", "private")

    assert result.returncode != 0
    assert "conflicting" in result.stderr
