variable "env" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "alarm_duration_threshold_ms" {
  type = number
}

variable "alert_topic_arn" {
  description = "SNS topic ARN to notify when the alarm fires"
  type        = string
}
