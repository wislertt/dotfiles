from bakelib.space import FnoxSpace, GitHubActionsTools, PythonSpace, SubmodulesUtils

from src.python.commands.apply import ApplyMixin
from src.python.commands.lint import LintMixin
from src.python.commands.machine import MachineMixin
from src.python.commands.macos_settings import MacosSettingsMixin
from src.python.commands.managed_content import ManagedContentMixin
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
    ManagedContentMixin,
    GitHubActionsTools,
    SubmodulesUtils,
    FnoxSpace[str | None],
    PythonSpace,
):
    bake_manage_content: bool = True
    jactionlint_profile = "pedantic"


bakebook = MyBakebook()
