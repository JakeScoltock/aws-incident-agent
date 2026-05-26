# AWS Incident Agent

An agentic AI system that automatically investigates AWS incidents and opens remediation PRs —
no autonomous deployment, no auto-merge. The PR is the safety boundary.

The demo scenario is a Lambda timeout regression, but the architecture applies to any AWS
incident type: errors, throttles, latency regressions, cost spikes, and more.

Built with Amazon Bedrock AgentCore Runtime, Strands Agents SDK, and AWS serverless infrastructure.

## Architecture

```
CloudWatch Alarm (Lambda duration threshold)
    │
    ▼
EventBridge Rule
    │
    ▼
Step Functions — Incident Workflow
    │
    ├── InvokeInvestigator → AgentCore Runtime
    │       Tools: CloudWatch metrics, Logs Insights, deployment history
    │       Output: IncidentReport (confidence score)
    │
    ├── EvaluateConfidence (Choice state)
    │       high → InvokeRemediation
    │       low  → PublishAlert (SNS)
    │
    └── InvokeRemediation → AgentCore Runtime
            Tools: GitHub read/write (branch, commit, PR)
            Output: RemediationReport (PR URL)
```

Two agents with cleanly separated concerns:
- **Investigator**: reads CloudWatch and deployment history, produces a structured `IncidentReport`
- **Remediation**: reads and writes GitHub, opens a PR with the proposed fix

## Setup

### Prerequisites

- [VS Code](https://code.visualstudio.com/) with the Dev Containers extension
- Docker
- AWS credentials in `~/.aws`

### Dev container

1. Open the repo in VS Code
2. Run **Dev Containers: Reopen in Container**
3. The container installs Python 3.13, AWS CLI v2, Terraform 1.12, GitHub CLI, ruff, and pytest

Verify the environment:

```bash
python --version   # 3.13.x
aws --version
terraform --version
gh --version
ruff --version
pytest --version
```

### Install project dependencies

```bash
pip install -e ".[dev]"
```

### Run linter and tests

```bash
ruff check .
ruff format --check .
pytest tests/
```

## CI/CD

- **CI** (`ci.yml`): runs on every push and PR — lint, format check, pytest
- **Deploy** (`deploy.yml`): runs on push to `main` — ECR push + Terraform apply (scaffold only)

## Project structure

```
aws-incident-agent/
├── .devcontainer/          Dev container (Python 3.13 + tooling)
├── .github/workflows/      CI and deploy pipelines
├── services/
│   ├── demo_api/           Lambda with deliberate timeout (example incident scenario)
│   ├── agents/
│   │   ├── investigator/   Strands agent + BedrockAgentCoreApp
│   │   └── remediation/    Strands agent + BedrockAgentCoreApp
│   ├── tools/
│   │   ├── aws_observability/  CloudWatch + DynamoDB tools
│   │   └── github/             GitHub REST API tools
│   └── shared/             Pydantic models + config
├── infra/terraform/        All AWS infrastructure
├── workflows/              Step Functions ASL definition
├── prompts/                Agent system prompts (markdown)
├── tests/
└── docs/PLAN.md            Full architecture plan
```

## Status

- [x] Repo foundation (devcontainer, CI/CD, pyproject.toml)
- [ ] Demo API Lambda + CloudWatch alarm
- [ ] Investigator agent
- [ ] Remediation agent
- [ ] Step Functions workflow
- [ ] End-to-end integration
