output "state_machine_arn" {
  value = aws_sfn_state_machine.incident_pipeline.arn
}

output "state_machine_name" {
  value = aws_sfn_state_machine.incident_pipeline.name
}

output "investigator_adapter_arn" {
  value = aws_lambda_function.investigator_adapter.arn
}

output "remediation_adapter_arn" {
  value = aws_lambda_function.remediation_adapter.arn
}
