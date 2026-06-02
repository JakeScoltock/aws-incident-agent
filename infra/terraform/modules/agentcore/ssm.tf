resource "aws_ssm_parameter" "github_token" {
  name        = "/incident-agent/${var.env}/github-token"
  description = "GitHub token for the remediation agent to create PRs"
  type        = "SecureString"
  value       = var.github_token
}

resource "aws_ssm_parameter" "github_repo" {
  name        = "/incident-agent/${var.env}/github-repo"
  description = "Target GitHub repository (owner/repo) for the remediation agent"
  type        = "String"
  value       = var.github_repo
}
