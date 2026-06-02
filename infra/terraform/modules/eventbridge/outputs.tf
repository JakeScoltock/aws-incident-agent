output "rule_arn" {
  value = aws_cloudwatch_event_rule.alarm_state_change.arn
}

output "rule_name" {
  value = aws_cloudwatch_event_rule.alarm_state_change.name
}
