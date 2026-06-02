data "archive_file" "placeholder" {
  type        = "zip"
  source_file = "${path.module}/lambda/placeholder.py"
  output_path = "${path.module}/lambda/placeholder.zip"
}

resource "aws_lambda_function" "investigator_adapter" {
  function_name    = "incident-agent-investigator-adapter-${var.env}"
  filename         = data.archive_file.placeholder.output_path
  source_code_hash = data.archive_file.placeholder.output_base64sha256
  role             = aws_iam_role.investigator_adapter.arn
  handler          = "placeholder.handler"
  runtime          = "python3.13"
  timeout          = 900

  environment {
    variables = {
      ENV                     = var.env
      AGENTCORE_ROLE_ARN      = var.agentcore_investigator_role_arn
      AGENTCORE_ECR_IMAGE_URI = var.agentcore_investigator_ecr_url
    }
  }
}

resource "aws_lambda_function" "remediation_adapter" {
  function_name    = "incident-agent-remediation-adapter-${var.env}"
  filename         = data.archive_file.placeholder.output_path
  source_code_hash = data.archive_file.placeholder.output_base64sha256
  role             = aws_iam_role.remediation_adapter.arn
  handler          = "placeholder.handler"
  runtime          = "python3.13"
  timeout          = 900

  environment {
    variables = {
      ENV                     = var.env
      AGENTCORE_ROLE_ARN      = var.agentcore_remediation_role_arn
      AGENTCORE_ECR_IMAGE_URI = var.agentcore_remediation_ecr_url
    }
  }
}
