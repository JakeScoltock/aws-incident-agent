import logging
from pathlib import Path

from services.shared.config import settings
from services.shared.models import IncidentReport
from strands import Agent
from strands.models import BedrockModel

from services.tools.aws_observability import (
    get_deployment_history,
    get_lambda_metrics,
    query_lambda_logs,
)

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent.parent.parent / "prompts" / "investigator_system.md"


def _load_prompt() -> str:
    return _PROMPT_PATH.read_text()


def build_investigator_agent() -> Agent:
    return Agent(
        model=BedrockModel(model_id=settings.bedrock_model_id),
        tools=[get_lambda_metrics, query_lambda_logs, get_deployment_history],
        system_prompt=_load_prompt(),
        structured_output_model=IncidentReport,
    )
