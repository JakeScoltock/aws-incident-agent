FROM python:3.13-slim

RUN apt-get update && apt-get install -y curl unzip git nodejs npm && rm -rf /var/lib/apt/lists/*

# Claude Code CLI
RUN npm install -g @anthropic-ai/claude-code

# AWS CLI v2
RUN curl -sL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o awscliv2.zip \
    && unzip awscliv2.zip && ./aws/install && rm -rf awscliv2.zip aws/

# Terraform
RUN curl -sL https://releases.hashicorp.com/terraform/1.12.0/terraform_1.12.0_linux_amd64.zip \
    -o tf.zip && unzip tf.zip && mv terraform /usr/local/bin/ && rm tf.zip

# GitHub CLI
RUN curl -sL https://github.com/cli/cli/releases/download/v2.72.0/gh_2.72.0_linux_amd64.tar.gz \
    | tar xz && mv gh_*/bin/gh /usr/local/bin/

# uv (fast Python package manager, also provides uvx for MCP servers)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Python tools
RUN pip install --no-cache-dir ruff pytest pytest-cov
