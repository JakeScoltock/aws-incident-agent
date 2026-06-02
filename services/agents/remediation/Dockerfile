FROM public.ecr.aws/docker/library/python:3.13-slim

WORKDIR /app

# Install dependencies
COPY services/agents/remediation/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared code and tools
COPY services/shared/ services/shared/
COPY services/tools/github/ services/tools/github/
COPY services/__init__.py services/__init__.py
COPY services/tools/__init__.py services/tools/__init__.py

# Copy agent code
COPY services/agents/__init__.py services/agents/__init__.py
COPY services/agents/remediation/ services/agents/remediation/

# Copy prompts
COPY prompts/remediation_system.md prompts/remediation_system.md

# AgentCore Runtime expects the entrypoint to start the HTTP server
CMD ["python", "-m", "services.agents.remediation.app"]
