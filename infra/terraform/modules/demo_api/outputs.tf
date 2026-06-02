output "api_gateway_url" {
  value = aws_apigatewayv2_stage.default.invoke_url
}

output "lambda_arn" {
  value = aws_lambda_function.demo_api.arn
}

output "alarm_arn" {
  value = aws_cloudwatch_metric_alarm.lambda_duration.arn
}

output "alarm_name" {
  value = aws_cloudwatch_metric_alarm.lambda_duration.alarm_name
}
