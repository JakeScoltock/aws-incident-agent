# CLAUDE.md — AWS Incident Agent

## Project

Portfolio-grade agentic AI system that automatically investigates AWS incidents and opens
remediation PRs. Built with Amazon Bedrock AgentCore Runtime, Strands Agents SDK, and AWS
serverless infrastructure. The PR is the safety boundary — no auto-merge, no auto-deploy.

The demo scenario is a Lambda timeout regression, but the architecture is designed for any
AWS incident type (errors, throttles, cost spikes, latency regressions, etc.).

Full architecture plan: `docs/PLAN.md`

---

## Architecture (two-agent pipeline)

```
CloudWatch Alarm → EventBridge → Step Functions
    ├── Investigator Agent (AgentCore)   tools: CloudWatch metrics/logs, DynamoDB deployment history
    │       └── produces: IncidentReport (Pydantic, confidence 0–1)
    └── Remediation Agent (AgentCore)    tools: GitHub read + branch + commit + PR
            └── produces: RemediationReport (PR URL, never merges)
```

---

## Repository map

```
services/shared/models.py          All Pydantic models (IncidentContext, IncidentReport, etc.)
services/shared/config.py          Pydantic Settings (env/SSM config)
services/tools/aws_observability/  @tool functions — CloudWatch + DynamoDB
services/tools/github/             @tool functions — GitHub REST API via httpx
services/agents/investigator/      Strands Agent + BedrockAgentCoreApp entrypoint
services/agents/remediation/       Strands Agent + BedrockAgentCoreApp entrypoint
services/demo_api/handler.py       Lambda with deliberate time.sleep(28) — example incident scenario
workflows/incident_workflow.asl.json  Step Functions ASL definition
infra/terraform/                   All AWS infrastructure
prompts/                           Agent system prompts (markdown, loaded at runtime)
tests/                             unit/ uses moto + httpx mocks, integration/ uses LocalStack
```

---

## Commands

```bash
pip install -e ".[dev]"      # install project + dev deps
ruff check .                 # lint
ruff format .                # format
ruff format --check .        # format check (CI mode)
pytest tests/ --tb=short     # run tests
pytest tests/unit/           # unit tests only (no AWS needed)
```

---

## Coding conventions

- Python 3.13 — use modern syntax: `X | Y` unions, `list[str]` not `List[str]`, match statements
- Type-annotate all function signatures
- Pydantic v2 for all data models and config (no dataclasses)
- All agent tools decorated with `@tool` from `strands` — docstring is the tool spec the LLM sees, make it precise
- boto3 clients instantiated at call time (not module level) to support mocking
- `httpx` for all HTTP calls (not `requests`)
- No print statements — use `logging` with structured fields
- Line length: 100 (enforced by ruff)
- Ruff rules in effect: E, F, I, UP, B, SIM

---

## Git workflow

- **Always create a new branch for each feature, phase, or task** before writing any code
- Branch naming: `feat/<short-description>` (e.g. `feat/investigator-agent`, `feat/cloudwatch-tools`)
- Never commit directly to `main`
- PR description should reference the phase/task from `docs/PLAN.md`
- Commit messages: imperative mood, concise (`Add CloudWatch metrics tool`, not `Added...`)

```bash
git checkout -b feat/<description>
# ... do work ...
git add -p                   # stage hunks, not whole files blindly
git commit -m "..."
gh pr create --fill
```

---

## Agent patterns

```python
# Tool pattern — docstring drives the LLM tool spec
@tool
def get_lambda_metrics(function_name: str, metric_name: str,
                       start_time: str, end_time: str,
                       period_seconds: int = 300) -> dict:
    """Query CloudWatch metrics for a Lambda function.
    metric_name: Duration | Errors | Throttles | Invocations
    start_time/end_time: ISO 8601 strings"""
    ...

# Agent pattern
from strands import Agent
from strands.models import BedrockModel

agent = Agent(
    model=BedrockModel(model_id="claude-sonnet-4-6"),
    tools=[tool_a, tool_b],
    system_prompt=prompt_text,
    structured_output_model=IncidentReport,
)

# AgentCore entrypoint pattern
from bedrock_agentcore.runtime import BedrockAgentCoreApp
app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload: dict) -> dict:
    ...
```

---

## Safety boundaries (never violate)

- Never add a tool that merges a PR, deploys code, or applies Terraform
- Never run `terraform apply` without explicit user confirmation
- Never `git push --force`
- Never commit secrets, `.env` files, or `*.pem`/`*.key` files
- Remediation agent opens PRs only — the human merges
- `aws * delete` commands require explicit user confirmation before running
