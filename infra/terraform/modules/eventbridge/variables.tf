variable "env" {
  type = string
}

variable "alarm_name_prefix" {
  description = "Prefix filter for CloudWatch alarm names that should trigger the workflow"
  type        = string
}

variable "state_machine_arn" {
  type = string
}
