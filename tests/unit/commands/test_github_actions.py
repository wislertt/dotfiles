from src.python import bakefile
from tests.unit.conftest import FakeCtx


def test_slow_lint_checks_the_workflows_with_zizmor(
    bakebook: bakefile.MyBakebook, fake_ctx: FakeCtx
) -> None:
    bakebook._lint_slow()
    assert ["zizmor", "--no-progress", ".github/workflows"] in fake_ctx.commands


def test_zizmor_is_required_and_installed_by_the_tool_manager(
    bakebook: bakefile.MyBakebook,
) -> None:
    assert "zizmor" in bakebook._get_required_cli_tools()
    assert "zizmor" in bakebook._get_mise_tools()


def test_bakelibs_github_actions_tools_are_included(
    bakebook: bakefile.MyBakebook,
) -> None:
    assert {"actionlint", "npm:actions-up"} <= bakebook._get_mise_tools()
