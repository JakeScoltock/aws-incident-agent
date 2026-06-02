resource "aws_dynamodb_table" "deployment_history" {
  name         = "incident-agent-deployment-history-${var.env}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "function_name"
  range_key    = "deployed_at"

  attribute {
    name = "function_name"
    type = "S"
  }

  attribute {
    name = "deployed_at"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }
}
