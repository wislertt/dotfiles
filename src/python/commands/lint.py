import shutil
from pathlib import Path

from bakelib.space import PythonSpace

from src.python.core import brewfiles, dotfile_entries, machines, repo, shell_files


class LintMixin(PythonSpace):
    def _lint_fast(self) -> None:
        super()._lint_fast()
        self._lint_shell()
        self._assert_global_fnox_empty()
        self._lint_brewfiles()
        self._lint_secret_writers()

    def _lint_shell(self) -> None:
        # Same file types as the pre-commit shellcheck hook; ShellCheck cannot parse zsh, so `zsh -n`
        out = self.ctx.run(
            ["git", "ls-files", "-z"], capture_output=True, stream=False, echo=False
        ).stdout
        sh, zsh = shell_files.classify(filter(None, out.split("\0")))
        if sh:
            self.ctx.run(["shellcheck", "--", *sh])
        for name in zsh:
            self.ctx.run(["zsh", "-n", name])

    def _lint_brewfiles(self) -> None:
        if unknown := machines.unknown_roles(repo.ROOT):
            raise SystemExit(
                f"machines.toml: no Brewfile.<role> or keep.<role>.toml for {', '.join(unknown)}"
            )
        for brewfile in brewfiles.every_path(repo.ROOT):
            for number, line in enumerate(brewfile.read_text().splitlines(), 1):
                if not brewfiles.line_allowed(line):
                    raise SystemExit(
                        f'{brewfile.name}:{number}: only `cask "name"` lines (and `brew "mise"`) allowed'
                    )
            if shutil.which("brew"):
                self.ctx.run(
                    ["brew", "bundle", "list", "--file", str(brewfile), "--cask"]
                )

    def _lint_secret_writers(self) -> None:
        # A secret reaches a program at start, never through a file Apply writes
        if found := dotfile_entries.secret_writers(repo.ROOT):
            raise SystemExit(
                f"[dotfiles] entries that write a secret: {', '.join(found)}"
            )

    def _assert_global_fnox_empty(self) -> None:
        # Secrets come only from `bake secret get`; the global fnox config must stay unused
        path = Path.home() / ".config" / "fnox" / "config.toml"
        if not path.exists():
            return
        # fnox exits 0 either way, so judge by output
        secrets = self._fnox_out("list", "-c", str(path))
        providers = self._fnox_out("provider", "list", "-c", str(path))
        if providers or not secrets.startswith("No secrets defined"):
            raise SystemExit(f"Global fnox config is not empty: {path}. Clear it.")

    def _fnox_out(self, *args: str) -> str:
        cmd = ["fnox", "--no-color", "--no-daemon", *args]
        return self.ctx.run(
            cmd, capture_output=True, stream=False, echo=False
        ).stdout.strip()
