variable "env" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "alert_topic_arn" {
  type = string
}

variable "agentcore_investigator_role_arn" {
  description = "IAM role ARN for the investigator AgentCore runtime (set in Phase 4)"
  type        = string
  default     = ""
}

variable "agentcore_remediation_role_arn" {
  description = "IAM role ARN for the remediation AgentCore runtime (set in Phase 4)"
  type        = string
  default     = ""
}

variable "agentcore_investigator_ecr_url" {
  description = "ECR repository URL for the investigator agent image (set in Phase 4)"
  type        = string
  default     = ""
}

variable "agentcore_remediation_ecr_url" {
  description = "ECR repository URL for the remediation agent image (set in Phase 4)"
  type        = string
  default     = ""
}
