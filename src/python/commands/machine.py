import os
import shutil
import sys

import typer
from bake import console
from bakelib.space import BaseSpace

from src.python.core import machines, repo

IOREG = ("ioreg", "-rd1", "-c", "IOPlatformExpertDevice")
NAME_VAR = "DOTFILES_MACHINE_NAME"  # for CI, which has no private machine list
NO_NAME = "This machine has no name; run `bake setup-dev` to set one"


class MachineMixin(BaseSpace):
    def _machine_id(self) -> str | None:
        """The machine list's key: the serial number on macOS, the systemd machine ID elsewhere."""
        if not shutil.which(IOREG[0]):
            return machines.linux_id()
        out = self.ctx.run(
            list(IOREG), capture_output=True, stream=False, echo=False, check=False
        ).stdout
        return machines.serial(out or "")

    def _roles(self) -> list[str]:
        """This machine's roles from the private machine list."""
        if not machines.machine_list(repo.ROOT):
            return []
        return machines.roles(repo.ROOT, self._machine_id())

    def _known_machine_name(self) -> str | None:
        if found := os.environ.get(NAME_VAR):
            if not machines.NAME.fullmatch(found):
                raise SystemExit(f"{NAME_VAR}: use lowercase letters, digits and -")
            return found
        return machines.name(repo.ROOT, self._machine_id())

    def _machine_name(self) -> str:
        """This machine's name; every use of it goes through here, so an unnamed machine fails the same way."""
        found = self._known_machine_name()
        if found is None:
            raise SystemExit(NO_NAME)
        return found

    def _name_this_machine(self) -> str:
        """Setup's step: the name, asking for one and adding it to the private machine list when there is none."""
        if found := self._known_machine_name():
            return found
        machine_id = self._machine_id()
        if machine_id is None:
            raise SystemExit(f"No machine ID to name this machine by; set {NAME_VAR}")
        if not sys.stdin.isatty():
            raise SystemExit(f"{NO_NAME} in a terminal, or set {NAME_VAR}")
        while True:
            new = typer.prompt("Name this machine (lowercase letters, digits, -)")
            try:
                file = machines.add(repo.ROOT, machine_id, new)
            except ValueError as error:
                console.error(str(error))
                continue
            console.success(
                f"Named this machine {new!r} in {file.relative_to(repo.ROOT)}; commit the private repo"
            )
            return new
