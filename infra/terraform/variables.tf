variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "eu-west-1"
}

variable "env" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "github_token" {
  description = "GitHub personal access token used by the remediation agent to create PRs"
  type        = string
  sensitive   = true
}

variable "github_repo" {
  description = "Target GitHub repository in owner/repo format"
  type        = string
}

variable "alarm_duration_threshold_ms" {
  description = "Lambda Duration (Average) threshold in milliseconds that triggers the incident alarm"
  type        = number
  default     = 27000
}

variable "alert_email" {
  description = "Email address to subscribe to incident alerts (leave empty to skip)"
  type        = string
  default     = ""
}

variable "agentcore_investigator_runtime_id" {
  description = "AgentCore Runtime ID for the investigator (set after runtime creation, leave empty to keep placeholder)"
  type        = string
  default     = ""
}

variable "agentcore_remediation_runtime_id" {
  description = "AgentCore Runtime ID for the remediation agent (set after runtime creation, leave empty to keep placeholder)"
  type        = string
  default     = ""
}

variable "agentcore_investigator_runtime_arn" {
  description = "AgentCore Runtime ARN for the investigator (arn:aws:bedrock-agentcore:region:account:runtime/id)"
  type        = string
  default     = ""
}

variable "agentcore_remediation_runtime_arn" {
  description = "AgentCore Runtime ARN for the remediation agent (arn:aws:bedrock-agentcore:region:account:runtime/id)"
  type        = string
  default     = ""
}
