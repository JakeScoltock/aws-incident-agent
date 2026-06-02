import logging
from pathlib import Path

from strands import Agent
from strands.models import BedrockModel

from services.shared.config import settings
from services.shared.models import RemediationReport
from services.tools.github import (
    commit_file_to_github,
    create_github_branch,
    create_github_pull_request,
    list_github_directory,
    read_github_file,
)

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent.parent.parent / "prompts" / "remediation_system.md"


def _load_prompt() -> str:
    return _PROMPT_PATH.read_text()


def build_remediation_agent() -> Agent:
    return Agent(
        model=BedrockModel(model_id=settings.bedrock_model_id),
        tools=[
            read_github_file,
            list_github_directory,
            create_github_branch,
            commit_file_to_github,
            create_github_pull_request,
        ],
        system_prompt=_load_prompt(),
        structured_output_model=RemediationReport,
    )
