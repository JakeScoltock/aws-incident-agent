data "archive_file" "demo_api" {
  type        = "zip"
  source_file = "${path.root}/../../services/demo_api/handler.py"
  output_path = "${path.module}/demo_api_lambda.zip"
}

resource "aws_lambda_function" "demo_api" {
  function_name    = "incident-agent-demo-api-${var.env}"
  description      = "Demo API with deliberate timeout regression for incident simulation"
  role             = aws_iam_role.demo_api.arn
  filename         = data.archive_file.demo_api.output_path
  source_code_hash = data.archive_file.demo_api.output_base64sha256
  handler          = "handler.lambda_handler"
  runtime          = "python3.13"
  timeout          = 30

  environment {
    variables = {
      ENV = var.env
    }
  }
}
