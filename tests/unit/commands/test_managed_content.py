from src.python import bakefile
from src.python.commands.managed_content import SECURITY_WORKFLOW


def test_security_workflow_is_detached(bakebook: bakefile.MyBakebook) -> None:
    assert bakebook._get_managed_files()[SECURITY_WORKFLOW].detached


def test_other_managed_files_stay_managed(bakebook: bakefile.MyBakebook) -> None:
    files = bakebook._get_managed_files()
    assert [path for path, f in files.items() if f.detached] == [SECURITY_WORKFLOW]
