from bake.utils.settings import PlatformType
from bakelib.space import BaseSpace

from src.python.core import macos_settings as core
from src.python.core import repo


class MacosSettingsMixin(BaseSpace):
    def _macos_settings(self, platform: PlatformType) -> None:
        """Runs each settings script whose content changed since it last succeeded."""
        if platform != "macos":
            return
        for script in core.scripts(repo.ROOT):
            if core.changed(repo.ROOT, script):
                self.ctx.run(["bash", str(script)])
                if not self.ctx.dry_run:
                    core.record(repo.ROOT, script)
