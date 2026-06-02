output "deployment_history_table_arn" {
  value = aws_dynamodb_table.deployment_history.arn
}

output "deployment_history_table_name" {
  value = aws_dynamodb_table.deployment_history.name
}

output "demo_api_log_group_name" {
  value = aws_cloudwatch_log_group.demo_api.name
}

output "alert_topic_arn" {
  value = aws_sns_topic.alerts.arn
}
