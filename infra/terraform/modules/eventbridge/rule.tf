resource "aws_cloudwatch_event_rule" "alarm_state_change" {
  name        = "incident-agent-alarm-trigger-${var.env}"
  description = "Trigger incident pipeline when a monitored CloudWatch alarm enters ALARM state"

  event_pattern = jsonencode({
    source        = ["aws.cloudwatch"]
    "detail-type" = ["CloudWatch Alarm State Change"]
    detail = {
      state = {
        value = ["ALARM"]
      }
      alarmName = [{
        prefix = var.alarm_name_prefix
      }]
    }
  })
}

resource "aws_cloudwatch_event_target" "step_functions" {
  rule      = aws_cloudwatch_event_rule.alarm_state_change.name
  target_id = "IncidentAgentStateMachine"
  arn       = var.state_machine_arn
  role_arn  = aws_iam_role.eventbridge.arn
}
