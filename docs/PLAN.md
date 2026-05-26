# AWS Incident Agent — Architecture Plan

## 1. Recommended Architecture

```
CloudWatch Alarm (Lambda duration/error threshold)
    │
    ▼
EventBridge Rule
    │
    ▼
Step Functions — Incident Workflow (ASL)
    │
    ├── State: InvokeInvestigator
    │       │
    │       ▼
    │   Lambda Adapter → AgentCore Runtime (Investigator Agent)
    │       │               Strands Agent + Tools:
    │       │               - CloudWatchMetricsTool
    │       │               - CloudWatchLogsInsightsTool
    │       │               - DeploymentHistoryTool
    │       │
    │       Returns: IncidentReport (Pydantic, structured JSON)
    │
    ├── State: EvaluateConfidence (Choice)
    │       high confidence → InvokeRemediation
    │       low confidence  → PublishAlert (SNS)
    │
    └── State: InvokeRemediation
            │
            ▼
        Lambda Adapter → AgentCore Runtime (Remediation Agent)
            │               Strands Agent + Tools:
            │               - GitHubRepoReadTool
            │               - GitHubBranchTool
            │               - GitHubCommitTool
            │               - GitHubPullRequestTool
            │
            Returns: RemediationReport (PR URL, branch, files changed)
```

**Key design decisions:**

- Step Functions invokes agents via a thin Lambda adapter (calls `InvokeAgentRuntime` via boto3).
  This is more pragmatic than relying on SDK integration availability for the new AgentCore service.
- Tools are `@tool`-decorated Python functions bundled directly inside each agent container
  (simpler than Gateway for MVP; avoids unnecessary service complexity).
- AgentCore Gateway is deferred to iteration 2 — it adds real value for GitHub OAuth egress
  credential management but is not required for a working MVP.
- Two agents only. Reasoning and remediation are cleanly separated concerns.
- Deployment history is stored in DynamoDB, written by the demo API CI/CD pipeline (simulated).

---

## 2. Repository Structure

```
aws-incident-agent/
├── .devcontainer/
│   ├── devcontainer.json
│   └── Dockerfile
├── .github/
│   └── workflows/
│       ├── ci.yml                    # lint, test, build
│       └── deploy.yml                # terraform apply + ECR push
├── services/
│   ├── demo_api/
│   │   ├── handler.py                # Lambda with deliberate timeout (example incident scenario)
│   │   └── requirements.txt
│   ├── agents/
│   │   ├── investigator/
│   │   │   ├── app.py                # BedrockAgentCoreApp entrypoint
│   │   │   ├── agent.py              # Strands Agent definition + tools
│   │   │   ├── prompts.py            # System prompt (loaded from /prompts)
│   │   │   ├── Dockerfile
│   │   │   └── requirements.txt
│   │   └── remediation/
│   │       ├── app.py
│   │       ├── agent.py
│   │       ├── prompts.py
│   │       ├── Dockerfile
│   │       └── requirements.txt
│   ├── tools/
│   │   ├── aws_observability/
│   │   │   ├── __init__.py
│   │   │   ├── cloudwatch_metrics.py
│   │   │   ├── cloudwatch_logs.py
│   │   │   └── deployment_history.py
│   │   └── github/
│   │       ├── __init__.py
│   │       ├── repo_read.py
│   │       ├── branch.py
│   │       ├── commit.py
│   │       └── pull_request.py
│   └── shared/
│       ├── __init__.py
│       ├── models.py                 # All Pydantic models
│       └── config.py                 # Environment config (Pydantic Settings)
├── infra/
│   └── terraform/
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       ├── backend.tf
│       └── modules/
│           ├── demo_api/             # Lambda + API GW + CW alarm
│           ├── agentcore/            # ECR repos + AgentCore resources + IAM
│           ├── step_functions/       # State machine + IAM
│           ├── eventbridge/          # Rule + target (triggers Step Functions)
│           └── observability/        # DynamoDB deployment-history table
├── workflows/
│   └── incident_workflow.asl.json   # Step Functions ASL definition
├── prompts/
│   ├── investigator_system.md
│   └── remediation_system.md
├── tests/
│   ├── unit/
│   │   ├── tools/
│   │   └── shared/
│   ├── integration/
│   └── conftest.py
├── docs/
│   └── PLAN.md
├── pyproject.toml
├── README.md
└── .gitignore
```

---

## 3. Step-by-Step MVP Build Plan

### Phase 1 — Foundation (Tasks 1–3)
1. **Dev Container** — `.devcontainer/` setup (Dockerfile + devcontainer.json)
2. **Project scaffold** — `pyproject.toml`, `.gitignore`, `README.md`, `services/shared/models.py`
3. **Demo API Lambda** — `services/demo_api/handler.py` with deliberate timeout bug

### Phase 2 — Infrastructure Skeleton (Tasks 4–7)
4. **Terraform base** — backend config, variables, provider, modules scaffold
5. **Demo API infra** — Lambda + API GW + CloudWatch alarm + EventBridge rule via Terraform
6. **Observability infra** — DynamoDB deployment history table + CloudWatch log groups
7. **AgentCore infra** — ECR repos, IAM roles for agents, AgentCore Runtime resources

### Phase 3 — Tools (Tasks 8–11)
8. **CloudWatch tools** — `cloudwatch_metrics.py`, `cloudwatch_logs.py` (boto3 + `@tool`)
9. **Deployment history tool** — `deployment_history.py` (DynamoDB reader + `@tool`)
10. **GitHub read tools** — `repo_read.py` (GitHub API via `httpx` + `@tool`)
11. **GitHub write tools** — `branch.py`, `commit.py`, `pull_request.py` (+ `@tool`)

### Phase 4 — Agents (Tasks 12–15)
12. **Shared models** — All Pydantic models, config (Pydantic Settings)
13. **Investigator Agent** — Strands Agent + BedrockAgentCoreApp + system prompt + Dockerfile
14. **Remediation Agent** — Strands Agent + BedrockAgentCoreApp + system prompt + Dockerfile
15. **Step Functions workflow** — ASL definition + Lambda adapter functions + Terraform

### Phase 5 — Integration + CI/CD (Tasks 16–18)
16. **Lambda adapters** — Two small Lambdas that call `InvokeAgentRuntime` (boto3)
17. **GitHub Actions** — CI (lint + test), CD (ECR push + terraform apply)
18. **End-to-end test** — Trigger fake alarm → verify PR created

---

## 4. Strands + AgentCore Integration Pattern

```python
# services/agents/investigator/app.py
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from .agent import build_investigator_agent

app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload: dict) -> dict:
    agent = build_investigator_agent()
    incident_context = payload["incident_context"]
    result = agent(f"Investigate this incident: {incident_context}")
    return result.structured_output.model_dump()

if __name__ == "__main__":
    app.run()
```

```python
# services/agents/investigator/agent.py
from strands import Agent
from strands.models import BedrockModel
from services.tools.aws_observability import (
    get_lambda_metrics, query_lambda_logs, get_deployment_history
)
from services.shared.models import IncidentReport

def build_investigator_agent() -> Agent:
    return Agent(
        model=BedrockModel(model_id="claude-sonnet-4-6"),
        tools=[get_lambda_metrics, query_lambda_logs, get_deployment_history],
        system_prompt=load_prompt("investigator_system.md"),
        structured_output_model=IncidentReport,
    )
```

**Key pattern**: `BedrockAgentCoreApp` wraps the Strands agent, handles HTTP `/invocations`
and `/ping` endpoints required by the AgentCore Runtime container protocol.

---

## 5. Step Functions vs Agent Responsibilities

| Concern | Step Functions | Agent |
|---|---|---|
| Workflow sequencing | ✓ | |
| Retry with backoff | ✓ | |
| Audit trail / execution history | ✓ | |
| Timeout management (workflow level) | ✓ | |
| Confidence threshold evaluation | ✓ (Choice state) | |
| Passing data between stages | ✓ | |
| Tool selection and invocation | | ✓ |
| Reasoning loops | | ✓ |
| Root cause identification | | ✓ |
| Code change generation | | ✓ |
| Structured output validation | | ✓ (Pydantic) |

---

## 6. Key Modules and Responsibilities

| Module | Responsibility |
|---|---|
| `services/demo_api/handler.py` | Lambda with deliberate `time.sleep()` — example incident scenario simulating a production regression |
| `services/shared/models.py` | All Pydantic models: `IncidentContext`, `IncidentReport`, `RemediationRequest`, `RemediationReport` |
| `services/shared/config.py` | Pydantic Settings: AWS region, GitHub token (from SSM/env), DynamoDB table name |
| `services/tools/aws_observability/` | `@tool` functions wrapping boto3 CloudWatch and DynamoDB calls |
| `services/tools/github/` | `@tool` functions wrapping GitHub REST API (via `httpx`) |
| `services/agents/investigator/agent.py` | Strands Agent with CW tools, structured output → `IncidentReport` |
| `services/agents/remediation/agent.py` | Strands Agent with GitHub tools, structured output → `RemediationReport` |
| `services/agents/*/app.py` | `BedrockAgentCoreApp` entrypoint (HTTP server wrapping agent) |
| `workflows/incident_workflow.asl.json` | Step Functions ASL — full workflow definition |
| `infra/terraform/` | All AWS infrastructure as code |
| `prompts/` | System prompts as markdown files (loaded at runtime) |

---

## 7. Terraform Component Plan

```
infra/terraform/
├── backend.tf          S3 + DynamoDB remote state
├── main.tf             Module composition
├── variables.tf        github_token (sensitive), aws_region, env
├── outputs.tf          step_functions_arn, api_gateway_url
└── modules/
    ├── demo_api/
    │   ├── lambda.tf       Lambda function + Layer
    │   ├── api_gateway.tf  HTTP API GW → Lambda
    │   ├── alarms.tf       CW Alarm: p99 Duration > threshold
    │   └── iam.tf          Lambda execution role
    ├── agentcore/
    │   ├── ecr.tf          Two ECR repos (investigator, remediation)
    │   ├── agentcore.tf    AgentCore Runtime resources (aws_bedrock_agent_runtime)
    │   └── iam.tf          AgentCore execution roles + Bedrock/CW/DynamoDB permissions
    ├── step_functions/
    │   ├── state_machine.tf  State machine from ASL file
    │   ├── adapters.tf       Two Lambda adapter functions
    │   └── iam.tf            Step Functions + Lambda execution roles
    ├── eventbridge/
    │   ├── rule.tf           CloudWatch Alarm → EventBridge → Step Functions
    │   └── target.tf
    └── observability/
        ├── dynamodb.tf       deployment_history table (pk: function_name, sk: deployed_at)
        └── log_groups.tf     CW log groups for all Lambdas
```

---

## 8. Step Functions Workflow Design (ASL Summary)

```
StartAt: ParseIncidentEvent
States:
  ParseIncidentEvent (Pass)
    → InvokeInvestigatorAdapter

  InvokeInvestigatorAdapter (Task → Lambda)
    Resource: arn:aws:states:::lambda:invoke
    Retry: MaxAttempts=2, BackoffRate=2, interval=5s
    ResultPath: $.incident_report
    → EvaluateConfidence

  EvaluateConfidence (Choice)
    $.incident_report.confidence >= 0.7  → InvokeRemediationAdapter
    default                              → PublishLowConfidenceAlert

  InvokeRemediationAdapter (Task → Lambda)
    Resource: arn:aws:states:::lambda:invoke
    Retry: MaxAttempts=1
    ResultPath: $.remediation_report
    → PublishSuccess

  PublishLowConfidenceAlert (Task → SNS)
    → WorkflowComplete

  PublishSuccess (Task → SNS)
    → WorkflowComplete

  WorkflowComplete (Succeed)
```

Lambda adapters call `bedrock-agentruntime:InvokeAgentRuntime` with the payload and
return the agent's structured JSON response to Step Functions.

---

## 9. Pydantic Models (services/shared/models.py)

```python
class IncidentContext(BaseModel):
    alarm_name: str
    lambda_function_name: str
    alarm_timestamp: datetime
    region: str
    account_id: str

class DeploymentRecord(BaseModel):
    deployment_id: str
    deployed_at: datetime
    deployed_by: str
    commit_sha: str
    branch: str

class IncidentReport(BaseModel):
    incident_id: str
    lambda_function_name: str
    root_cause_summary: str
    evidence: list[str]
    deployment_correlation: DeploymentRecord | None
    affected_files: list[str]
    recommended_action: str
    confidence: float           # 0.0–1.0
    created_at: datetime

class RemediationRequest(BaseModel):
    incident_report: IncidentReport
    github_repo: str            # e.g. "owner/repo"
    base_branch: str = "main"

class RemediationReport(BaseModel):
    incident_id: str
    branch_name: str
    commit_sha: str
    pr_url: str
    pr_number: int
    changes_summary: str
    files_modified: list[str]
    created_at: datetime
```

---

## 10. Tool Interface Design

All tools are `@tool`-decorated functions. Type annotations and docstrings drive the
tool spec the LLM sees.

**Investigator tools:**
```python
@tool
def get_lambda_metrics(function_name: str, metric_name: str,
                       start_time: str, end_time: str,
                       period_seconds: int = 300) -> dict:
    """Query CloudWatch metrics for a Lambda function.
    metric_name: Duration | Errors | Throttles | Invocations
    start_time/end_time: ISO 8601 strings"""

@tool
def query_lambda_logs(function_name: str, query: str,
                      start_time: str, end_time: str,
                      limit: int = 100) -> dict:
    """Run a CloudWatch Logs Insights query against a Lambda log group."""

@tool
def get_deployment_history(function_name: str,
                           lookback_hours: int = 24) -> dict:
    """Retrieve recent deployment records for a Lambda from DynamoDB."""
```

**Remediation tools:**
```python
@tool
def read_github_file(repo: str, path: str, ref: str = "main") -> dict:
    """Read a file from a GitHub repository."""

@tool
def list_github_directory(repo: str, path: str = "",
                          ref: str = "main") -> dict:
    """List files in a GitHub repository directory."""

@tool
def create_github_branch(repo: str, branch_name: str,
                         from_ref: str = "main") -> dict:
    """Create a new branch in a GitHub repository."""

@tool
def commit_file_to_github(repo: str, branch: str, path: str,
                           content: str, message: str) -> dict:
    """Commit a file change to a GitHub branch."""

@tool
def create_github_pull_request(repo: str, head_branch: str,
                                base_branch: str, title: str,
                                body: str) -> dict:
    """Open a GitHub Pull Request. Does not merge."""
```

---

## 11. Testing Strategy

**Unit tests** (`tests/unit/`):
- Mock `boto3` clients with `moto` for CloudWatch and DynamoDB tools
- Mock `httpx` responses for GitHub tools
- Test Pydantic model validation (valid inputs, edge cases)
- Run with `pytest` — fast, no AWS credentials needed

**Integration tests** (`tests/integration/`):
- CloudWatch/DynamoDB tools against LocalStack
- GitHub tools against a real test repo (controlled via env var)
- Agent instantiation smoke test (no Bedrock call, just verify tool registration)

**Agent evaluation** (`evaluation/`):
- Synthetic incident fixtures (pre-built CloudWatch data + deployment records)
- Assert `IncidentReport.confidence` above threshold for known bug patterns
- Assert `RemediationReport.pr_url` is non-empty for a known test repo

**CI (`ci.yml`):** `ruff check` → `pytest tests/unit` → Docker build (no push)

**CD (`deploy.yml`):** `terraform plan` on PR, `terraform apply` + ECR push on merge to main

---

## 12. Risks and Scope Boundaries

**Technical risks:**
- AgentCore Runtime Terraform resource (`aws_bedrockagent_*`) support — may require
  AWS CLI / boto3 calls in a custom resource Lambda if Terraform provider lags
- `InvokeAgentRuntime` API name/shape may differ slightly from docs — verify against
  latest boto3 `bedrock-agentruntime` service model before coding adapters
- Remediation agent writing code changes is inherently risky — prompt must explicitly
  forbid merging PRs and deploying; the tool set enforces this by omitting merge/deploy tools

**Out of MVP scope:**
- Frontend / dashboard
- Slack / PagerDuty notifications (SNS is sufficient)
- AgentCore Gateway (deferred to iteration 2)
- Multi-incident handling or queue
- Generic coding agent
- Auto-merge or auto-deploy
- Multiple incident types
- Multi-agent swarm

---

## 13. Verification Plan (End-to-End)

1. Invoke demo API endpoint → Lambda times out → CloudWatch alarm ALARM state
2. EventBridge rule fires → Step Functions execution starts (visible in console)
3. Step Functions invokes Investigator Lambda adapter → AgentCore Runtime runs
4. Investigator returns `IncidentReport` JSON with `confidence >= 0.7`
5. Step Functions transitions to Remediation stage
6. Remediation agent creates branch, commits fix, opens PR on GitHub test repo
7. PR URL appears in Step Functions execution output and SNS notification
8. Human reviews PR — no auto-merge occurs
