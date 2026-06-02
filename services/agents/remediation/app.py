import logging

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from services.shared.models import IncidentReport, RemediationRequest

from .agent import build_remediation_agent

logger = logging.getLogger(__name__)

app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload: dict) -> dict:
    request = RemediationRequest.model_validate(payload)
    agent = build_remediation_agent()

    report: IncidentReport = request.incident_report
    prompt = (
        f"Remediate this AWS incident:\n\n"
        f"Incident ID: {report.incident_id}\n"
        f"Lambda function: {report.lambda_function_name}\n"
        f"Root cause: {report.root_cause_summary}\n"
        f"Affected files: {report.affected_files}\n"
        f"Recommended action: {report.recommended_action}\n"
        f"GitHub repo: {request.github_repo}\n"
        f"Base branch: {request.base_branch}\n\n"
        f"Use your tools to open a PR that fixes the root cause. "
        f"Return a structured RemediationReport."
    )

    logger.info("starting remediation", extra={"incident_id": report.incident_id})
    result = agent(prompt)
    remediation = result.structured_output
    logger.info("remediation complete", extra={"pr_url": remediation.pr_url})
    return remediation.model_dump(mode="json")


if __name__ == "__main__":
    app.run()
