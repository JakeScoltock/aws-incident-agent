import logging

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from services.shared.models import IncidentContext

from .agent import build_investigator_agent

logger = logging.getLogger(__name__)

app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload: dict) -> dict:
    context = IncidentContext.model_validate(payload["incident_context"])
    agent = build_investigator_agent()

    prompt = (
        f"Investigate this AWS incident:\n\n"
        f"Alarm: {context.alarm_name}\n"
        f"Lambda function: {context.lambda_function_name}\n"
        f"Alarm timestamp: {context.alarm_timestamp.isoformat()}\n"
        f"Region: {context.region}\n"
        f"Account: {context.account_id}\n\n"
        f"Use your tools to determine the root cause and return a structured IncidentReport."
    )

    logger.info("starting investigation", extra={"alarm": context.alarm_name})
    result = agent(prompt)
    report = result.structured_output
    logger.info("investigation complete", extra={"confidence": report.confidence})
    return report.model_dump(mode="json")


if __name__ == "__main__":
    app.run()
