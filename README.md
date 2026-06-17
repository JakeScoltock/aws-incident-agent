# AWS Incident Agent

An agentic AI system that automatically investigates AWS incidents and opens remediation PRs — no autonomous deployment, no auto-merge. The PR is the safety boundary.

## What it does

A CloudWatch alarm fires. Within seconds, an investigator agent queries CloudWatch metrics and Logs Insights, correlates the incident with recent deployment history, and produces a structured report with a confidence score. If confidence is high enough, a remediation agent reads the affected files in GitHub, writes a targeted fix, and opens a PR for a human to review and merge.

The demo scenario is a Lambda timeout regression, but the pipeline is designed for any AWS incident type: errors, throttles, latency regressions, cost spikes, and more.

## Key features

- **Two-agent pipeline** — investigator and remediation with cleanly separated concerns and structured Pydantic outputs
- **Confidence-gated remediation** — Step Functions only invokes the remediation agent if the investigator returns confidence ≥ 0.5
- **Structured outputs** — `IncidentReport` and `RemediationReport` Pydantic models enforce schema across the pipeline
- **AgentCore runtime** — agents run as containerised, versioned runtimes on Amazon Bedrock AgentCore with automatic scaling
- **Full CI/CD** — GitHub Actions builds ECR images, updates AgentCore runtimes, and applies Terraform on every merge to main
- **Hard safety boundary** — the remediation agent can only open PRs; no tool merges code, deploys infrastructure, or runs shell commands

## Architecture

```
CloudWatch Alarm
    │
    ▼
EventBridge Rule
    │
    ▼
Step Functions — Incident Workflow
    │
    ├── Investigate → Lambda Adapter → AgentCore Runtime
    │       Tools: CloudWatch metrics, Logs Insights, DynamoDB deployment history
    │       Output: IncidentReport { root_cause_summary, evidence, confidence }
    │
    ├── CheckConfidence (Choice state)
    │       ≥ 0.5 → Remediate
    │       < 0.5 → NotifyLowConfidence (SNS)
    │
    └── Remediate → Lambda Adapter → AgentCore Runtime
            Tools: GitHub read + branch + commit + PR
            Output: RemediationReport { pr_url, files_modified, changes_summary }
                │
                ▼
            NotifySuccess (SNS) → human reviews and merges PR
```

## Tech stack

| Layer | Technology |
|---|---|
| Agent runtime | Amazon Bedrock AgentCore Runtime |
| Agent framework | Strands Agents SDK |
| LLM | Amazon Bedrock — Claude Sonnet 4.6 (EU cross-region inference) |
| Observability | CloudWatch Metrics + Logs Insights |
| Deployment history | Amazon DynamoDB |
| Workflow orchestration | AWS Step Functions (Standard) |
| Event routing | Amazon EventBridge |
| Notifications | Amazon SNS |
| Container registry | Amazon ECR |
| Infrastructure | Terraform |
| CI/CD | GitHub Actions + OIDC |

## Investigation flow

1. CloudWatch alarm breaches threshold → EventBridge rule fires → Step Functions execution starts.
2. `ExtractAlarmContext` (Pass state) reshapes the EventBridge event into a clean context object.
3. Investigator Lambda adapter invokes the AgentCore runtime with the incident context.
4. Agent queries CloudWatch metrics — Duration, Errors, Throttles, Invocations — over a 2-hour window around the alarm timestamp.
5. Agent runs Logs Insights queries against the Lambda log group: REPORT lines, error messages, `Task timed out after` patterns.
6. Agent queries DynamoDB deployment history to correlate the incident with a recent code change.
7. Structured `IncidentReport` returned: root cause summary, evidence list, affected files, recommended action, and confidence score (0–1).

## Remediation flow

1. `CheckConfidence` (Choice state) evaluates `investigation.body.confidence`.
2. If ≥ 0.5 → proceeds to remediation. If < 0.5 → SNS notification for manual review.
3. Remediation Lambda adapter invokes the AgentCore runtime with the incident report and GitHub repo details.
4. Agent reads the repository structure and the affected source files via GitHub REST API.
5. Agent creates a fix branch, commits a targeted code change, and opens a PR with a structured description.
6. Structured `RemediationReport` returned: branch name, commit SHA, PR URL, files modified, changes summary.
7. `NotifySuccess` publishes an SNS message with the root cause summary and PR link.

## Demo scenario

The demo API (`services/demo_api/handler.py`) has a `/slow` endpoint that deliberately sleeps 28 seconds, triggering the Lambda duration alarm. To run the full pipeline end-to-end:

```bash
# 1. Hit the slow endpoint to generate a high-duration invocation
curl https://<api-endpoint>/slow

# 2. Set the alarm to ALARM state to trigger the pipeline immediately
aws cloudwatch set-alarm-state \
  --region eu-west-1 \
  --alarm-name "incident-agent-dev-lambda-duration" \
  --state-value ALARM \
  --state-reason "Manual demo trigger"

# 3. Watch the Step Functions execution
aws stepfunctions list-executions \
  --region eu-west-1 \
  --state-machine-arn <state-machine-arn> \
  --max-results 1
```

The investigator identifies the `"Entering slow path"` warning log, correlates it with the 28-second REPORT duration, rules out errors and throttles, and produces a report. The remediation agent opens a PR that resets the sleep constant and adds a guard.

## Local development

```bash
# Install project + dev dependencies
pip install -e ".[dev]"

# Lint
ruff check .

# Format check
ruff format --check .

# Run all tests (no AWS credentials needed — all clients are mocked)
pytest tests/ --tb=short

# Unit tests only
pytest tests/unit/
```

Prerequisites: Python 3.13, Docker, VS Code with the Dev Containers extension. The devcontainer installs Python 3.13, AWS CLI v2, Terraform 1.12, GitHub CLI, ruff, and pytest automatically.

## Deployment

Infrastructure is managed with Terraform in `infra/terraform/`.

```bash
cd infra/terraform

# First-time state backend setup (one-off)
aws s3 mb s3://aws-incident-agent-tfstate --region eu-west-1

terraform init
terraform plan
terraform apply
```

Key Terraform variables:

| Variable | Description |
|---|---|
| `aws_region` | AWS region (default: `eu-west-1`) |
| `env` | Environment name used in resource naming (default: `dev`) |
| `github_token` | GitHub PAT stored in SSM — used by the remediation agent |
| `github_repo` | Target repository in `owner/repo` format |
| `alert_email` | SNS subscription address for incident notifications |

CI/CD runs automatically on merge to `main`: GitHub Actions builds and pushes ECR images, updates both AgentCore runtimes, and runs `terraform apply`.

## Project structure

```
aws-incident-agent/
├── services/
│   ├── agents/
│   │   ├── investigator/       Strands agent + BedrockAgentCoreApp entrypoint
│   │   └── remediation/        Strands agent + BedrockAgentCoreApp entrypoint
│   ├── tools/
│   │   ├── aws_observability/  @tool functions — CloudWatch metrics, Logs Insights, DynamoDB
│   │   └── github/             @tool functions — GitHub REST API (read, branch, commit, PR)
│   └── shared/                 Pydantic models (IncidentReport, RemediationReport) + config
├── infra/terraform/            All AWS infrastructure (VPC, ECR, AgentCore, Step Functions, SNS)
├── infra/terraform/modules/
│   └── step_functions/lambda/  Lambda adapter functions (bridge Step Functions → AgentCore)
├── prompts/                    Agent system prompts loaded at runtime
├── workflows/                  Step Functions ASL definition (reference)
├── scripts/                    AgentCore runtime management (called by Terraform local-exec)
└── tests/unit/                 36 unit tests — moto + httpx mocks, no AWS credentials needed
```

## Future improvements

- **Deployment history population** — instrument CI to write a DynamoDB record on every deploy, enabling the investigator to correlate incidents with specific commits
- **AgentCore env var support** — once the runtime API exposes container env vars, move SSM token fetching out of `model_post_init` and into standard config
- **Slack notification integration** — post incident summaries and PR links directly to an on-call channel
- **Multi-alarm support** — extend the pipeline to handle Errors, Throttles, and cost-spike alarms with alarm-type-specific investigation strategies
- **Agent evaluation framework** — score investigation quality against ground-truth incident labels to track regression across prompt versions
