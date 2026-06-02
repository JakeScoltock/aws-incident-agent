output "api_gateway_url" {
  description = "Demo API endpoint — hit /slow to trigger the incident scenario"
  value       = module.demo_api.api_gateway_url
}

output "step_functions_arn" {
  description = "Incident workflow state machine ARN"
  value       = module.step_functions.state_machine_arn
}

output "investigator_ecr_url" {
  description = "ECR repository URL for the investigator agent image"
  value       = module.agentcore.investigator_ecr_url
}

output "remediation_ecr_url" {
  description = "ECR repository URL for the remediation agent image"
  value       = module.agentcore.remediation_ecr_url
}

output "deployment_history_table_name" {
  description = "DynamoDB table name consumed by the get_deployment_history tool"
  value       = module.observability.deployment_history_table_name
}

output "alert_topic_arn" {
  description = "SNS topic ARN for incident and remediation notifications"
  value       = module.observability.alert_topic_arn
}
