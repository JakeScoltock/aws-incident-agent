resource "aws_cloudwatch_log_group" "demo_api" {
  name              = "/aws/lambda/incident-agent-demo-api-${var.env}"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "investigator_adapter" {
  name              = "/aws/lambda/incident-agent-investigator-adapter-${var.env}"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "remediation_adapter" {
  name              = "/aws/lambda/incident-agent-remediation-adapter-${var.env}"
  retention_in_days = 14
}
