resource "aws_apigatewayv2_api" "demo_api" {
  name          = "incident-agent-demo-api-${var.env}"
  protocol_type = "HTTP"
  description   = "Demo API endpoint for incident simulation"
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.demo_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.demo_api.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.demo_api.id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "root" {
  api_id    = aws_apigatewayv2_api.demo_api.id
  route_key = "ANY /"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

# Explicit deployment (replaces auto_deploy=true) so the $default stage is
# always in a known-deployed state and the execute-api DNS entry is created.
resource "aws_apigatewayv2_deployment" "main" {
  api_id = aws_apigatewayv2_api.demo_api.id

  depends_on = [
    aws_apigatewayv2_integration.lambda,
    aws_apigatewayv2_route.default,
    aws_apigatewayv2_route.root,
  ]

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_apigatewayv2_stage" "default" {
  api_id        = aws_apigatewayv2_api.demo_api.id
  name          = "$default"
  deployment_id = aws_apigatewayv2_deployment.main.id
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.demo_api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.demo_api.execution_arn}/*/*"
}
