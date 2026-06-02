data "archive_file" "investigator_adapter" {
  type        = "zip"
  source_file = "${path.module}/lambda/investigator_adapter.py"
  output_path = "${path.module}/lambda/investigator_adapter.zip"
}

data "archive_file" "remediation_adapter" {
  type        = "zip"
  source_file = "${path.module}/lambda/remediation_adapter.py"
  output_path = "${path.module}/lambda/remediation_adapter.zip"
}

resource "aws_lambda_function" "investigator_adapter" {
  function_name    = "incident-agent-investigator-adapter-${var.env}"
  filename         = data.archive_file.investigator_adapter.output_path
  source_code_hash = data.archive_file.investigator_adapter.output_base64sha256
  role             = aws_iam_role.investigator_adapter.arn
  handler          = "investigator_adapter.handler"
  runtime          = "python3.13"
  timeout          = 900

  environment {
    variables = {
      ENV                     = var.env
      AGENTCORE_RUNTIME_ID    = var.agentcore_investigator_runtime_id
      AGENTCORE_RUNTIME_ARN   = var.agentcore_investigator_runtime_arn
      MONITORED_FUNCTION_NAME = var.monitored_function_name
      AGENTCORE_ROLE_ARN      = var.agentcore_investigator_role_arn
      AGENTCORE_ECR_IMAGE_URI = var.agentcore_investigator_ecr_url
    }
  }
}

resource "aws_lambda_function" "remediation_adapter" {
  function_name    = "incident-agent-remediation-adapter-${var.env}"
  filename         = data.archive_file.remediation_adapter.output_path
  source_code_hash = data.archive_file.remediation_adapter.output_base64sha256
  role             = aws_iam_role.remediation_adapter.arn
  handler          = "remediation_adapter.handler"
  runtime          = "python3.13"
  timeout          = 900

  environment {
    variables = {
      ENV                     = var.env
      AGENTCORE_RUNTIME_ID    = var.agentcore_remediation_runtime_id
      AGENTCORE_RUNTIME_ARN   = var.agentcore_remediation_runtime_arn
      GITHUB_REPO_SSM_NAME    = var.github_repo_ssm_name
      AGENTCORE_ROLE_ARN      = var.agentcore_remediation_role_arn
      AGENTCORE_ECR_IMAGE_URI = var.agentcore_remediation_ecr_url
    }
  }
}
