variable "env" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "deployment_history_table_arn" {
  type = string
}

variable "deployment_history_table_name" {
  type = string
}

variable "github_token" {
  type      = string
  sensitive = true
}

variable "github_repo" {
  type = string
}

variable "image_tag" {
  description = "Image tag to deploy to AgentCore runtimes (defaults to latest; set to git SHA in CI)"
  type        = string
  default     = "latest"
}
