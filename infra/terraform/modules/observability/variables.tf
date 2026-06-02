variable "env" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "alert_email" {
  description = "Email address to subscribe to the incident alert SNS topic (leave empty to skip)"
  type        = string
  default     = ""
}
