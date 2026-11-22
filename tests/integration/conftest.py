import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
MISE = shutil.which("mise") or "mise"


def copy_repo(dest: Path, *, with_private: bool) -> Path:
    """Copy the repo's tracked and untracked files, so the working tree is never touched."""
    names = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split("\0")
    for name in filter(None, names):
        if name == "private":  # the submodule entry itself
            continue
        target = dest / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / name, target, follow_symlinks=False)
    if with_private:
        shutil.copytree(
            REPO / "private",
            dest / "private",
            symlinks=True,
            ignore=shutil.ignore_patterns(".git"),
        )
    return dest


class Machine:
    """A throwaway HOME plus a repo copy, running the real mise as `bake apply` does."""

    def __init__(self, root: Path, *, with_private: bool) -> None:
        self.repo = copy_repo(root / "repo", with_private=with_private)
        self.home = root / "home"
        self.home.mkdir()

    def apply(self, *flags: str) -> subprocess.CompletedProcess[str]:
        env = {
            **os.environ,
            "HOME": str(self.home),
            "MISE_TRUSTED_CONFIG_PATHS": str(self.repo),
            "MISE_DATA_DIR": str(Path(os.environ["HOME"]) / ".local/share/mise"),
        }
        return subprocess.run(
            [MISE, *flags, "dotfiles", "apply"],
            cwd=self.repo,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def links(self) -> dict[Path, Path]:
        return {
            p.relative_to(self.home): p.readlink()
            for p in sorted(self.home.rglob("*"))
            if p.is_symlink()
        }


@pytest.fixture
def public_machine(tmp_path: Path) -> Machine:
    return Machine(tmp_path, with_private=False)


@pytest.fixture
def private_machine(tmp_path: Path) -> Machine:
    if not (REPO / "private" / "src").is_dir():
        pytest.skip("no private companion checked out")
    return Machine(tmp_path, with_private=True)
