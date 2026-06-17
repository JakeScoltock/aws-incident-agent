import logging

import boto3
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


def _fetch_ssm(param_name: str, region: str) -> str:
    try:
        client = boto3.client("ssm", region_name=region)
        return client.get_parameter(Name=param_name, WithDecryption=True)["Parameter"]["Value"]
    except Exception as exc:
        logger.warning("SSM fetch failed", extra={"param": param_name, "error": str(exc)})
        return ""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="INCIDENT_AGENT_", case_sensitive=False)

    aws_region: str = "eu-west-1"
    deployment_history_table: str = "incident-agent-deployment-history"
    github_token: str = ""
    github_token_ssm_name: str = "/incident-agent/dev/github-token"
    bedrock_model_id: str = "eu.anthropic.claude-sonnet-4-6"

    def model_post_init(self, __context: object) -> None:
        if not self.github_token and self.github_token_ssm_name:
            object.__setattr__(
                self, "github_token", _fetch_ssm(self.github_token_ssm_name, self.aws_region)
            )


settings = Settings()
