from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="INCIDENT_AGENT_", case_sensitive=False)

    aws_region: str = "eu-west-1"
    deployment_history_table: str = "incident-agent-deployment-history"
    github_token: str = ""  # populated from SSM or env at runtime
    bedrock_model_id: str = "us.anthropic.claude-sonnet-4-6-20251001-v1:0"


settings = Settings()
