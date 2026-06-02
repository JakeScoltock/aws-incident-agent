resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  alarm_name          = "incident-agent-${var.env}-lambda-duration"
  alarm_description   = "Lambda average duration exceeds threshold — possible timeout regression"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Average"
  threshold           = var.alarm_duration_threshold_ms
  treat_missing_data  = "notBreaching"
  alarm_actions       = [var.alert_topic_arn]
  ok_actions          = [var.alert_topic_arn]

  dimensions = {
    FunctionName = aws_lambda_function.demo_api.function_name
  }
}
