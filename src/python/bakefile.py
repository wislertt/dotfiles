from bakelib.space import FnoxSpace, PythonSpace, SubmodulesUtils

from src.python.commands.apply import ApplyMixin
from src.python.commands.github_actions import GitHubActionsMixin
from src.python.commands.lint import LintMixin
from src.python.commands.machine import MachineMixin
from src.python.commands.macos_settings import MacosSettingsMixin
from src.python.commands.secrets import SecretsMixin
from src.python.commands.setup_update import SetupUpdateMixin
from src.python.commands.tidy import TidyMixin
from src.python.commands.tmp.uv_cache import UvCacheMixin


class MyBakebook(
    SecretsMixin,
    ApplyMixin,
    SetupUpdateMixin,
    LintMixin,
    MacosSettingsMixin,
    MachineMixin,
    TidyMixin,
    UvCacheMixin,
    GitHubActionsMixin,
    SubmodulesUtils,
    FnoxSpace[str | None],
    PythonSpace,
):
    pass


bakebook = MyBakebook()
