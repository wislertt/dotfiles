from bakelib.managed_content import ManagedFile
from bakelib.space import GitHubActionsTools

SECURITY_WORKFLOW = ".github/workflows/security.yml"


class ManagedContentMixin(GitHubActionsTools):
    def _get_managed_files(self) -> dict[str, ManagedFile]:
        files = super()._get_managed_files()
        # TODO: add name: to trivy-scan in bakefile's security.yml template, then drop this detach
        return {**files, SECURITY_WORKFLOW: files[SECURITY_WORKFLOW].detach()}
