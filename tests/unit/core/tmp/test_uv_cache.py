from pathlib import Path

from src.python.core.tmp import uv_cache


def _file(path: Path, size: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size)


def test_snapshot_lists_environments_with_their_packages(tmp_path: Path) -> None:
    _file(
        tmp_path
        / "environments-v2"
        / "e1"
        / "site-packages"
        / "pandas-2.3.0.dist-info"
        / "METADATA",
        10,
    )
    _file(tmp_path / "archive-v0" / "a1" / "ruff-0.9.0.dist-info" / "METADATA", 5)
    snap = uv_cache.snapshot(tmp_path, since=0)
    env = snap["entries"]["environments-v2"][0]
    assert env["path"] == "environments-v2/e1"
    assert env["packages"] == ["pandas"]
    assert snap["folders"]["archive-v0"] == {"bytes": 5, "files": 1}
    assert snap["unpacked_since_last"] == {"ruff": 1}


def test_unpacked_counts_only_entries_newer_than_the_last_run(tmp_path: Path) -> None:
    _file(tmp_path / "archive-v0" / "a1" / "ruff-0.9.0.dist-info" / "METADATA", 5)
    assert uv_cache.snapshot(tmp_path, since=None)["unpacked_since_last"] == {}
    assert uv_cache.snapshot(tmp_path, since=2**40)["unpacked_since_last"] == {}


def _snap(env_files: int = 0, archive_bytes: int = 0) -> dict:
    return {
        "folders": {
            "environments-v2": {"bytes": 0, "files": env_files},
            "archive-v0": {"bytes": archive_bytes, "files": 1},
        }
    }


def test_a_quiet_cache_has_no_problems() -> None:
    assert (
        uv_cache.problems(_snap(), _snap(env_files=10, archive_bytes=uv_cache.GIB))
        == []
    )


def test_a_full_environments_folder_is_a_problem() -> None:
    (found,) = uv_cache.problems(None, _snap(env_files=uv_cache.ENV_LIMIT_FILES + 1))
    assert found.startswith("environments-v2")


def test_fast_growth_since_the_last_run_is_a_problem() -> None:
    grew = _snap(archive_bytes=uv_cache.GROWTH_LIMIT_BYTES + 1)
    (found,) = uv_cache.problems(_snap(), grew)
    assert "grew" in found
