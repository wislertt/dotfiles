from pathlib import Path

from bakelib.space import GitHubActionsTools


# TODO: move zizmor into bakelib's GitHubActionsTools, then use that directly
class GitHubActionsMixin(GitHubActionsTools):
    def _get_mise_tools(self) -> set[str]:
        return super()._get_mise_tools() | {"zizmor"}

    def _get_required_cli_tools(self) -> dict[str, set[Path] | None]:
        tools = super()._get_required_cli_tools()
        tools["zizmor"] = None
        return tools

    def _lint_slow(self) -> None:
        super()._lint_slow()
        # slow with a GitHub token (online audits), so in lint -s, not the commit hook
        self.ctx.run(["zizmor", "--no-progress", ".github/workflows"])
