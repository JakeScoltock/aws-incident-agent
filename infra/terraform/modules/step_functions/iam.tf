data "aws_caller_identity" "current" {}

# ── Step Functions execution role ─────────────────────────────────────────────

data "aws_iam_policy_document" "sfn_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["states.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_iam_role" "sfn" {
  name               = "incident-agent-sfn-${var.env}"
  assume_role_policy = data.aws_iam_policy_document.sfn_assume.json
}

data "aws_iam_policy_document" "sfn" {
  statement {
    sid     = "InvokeLambdaAdapters"
    actions = ["lambda:InvokeFunction"]
    resources = [
      aws_lambda_function.investigator_adapter.arn,
      "${aws_lambda_function.investigator_adapter.arn}:*",
      aws_lambda_function.remediation_adapter.arn,
      "${aws_lambda_function.remediation_adapter.arn}:*",
    ]
  }

  statement {
    sid       = "PublishAlerts"
    actions   = ["sns:Publish"]
    resources = [var.alert_topic_arn]
  }

  statement {
    sid = "CloudWatchLogs"
    actions = [
      "logs:CreateLogDelivery",
      "logs:PutLogEvents",
      "logs:GetLogDelivery",
      "logs:UpdateLogDelivery",
      "logs:DeleteLogDelivery",
      "logs:ListLogDeliveries",
      "logs:PutResourcePolicy",
      "logs:DescribeResourcePolicies",
      "logs:DescribeLogGroups",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "sfn" {
  name   = "sfn-policy"
  role   = aws_iam_role.sfn.id
  policy = data.aws_iam_policy_document.sfn.json
}

# ── Lambda adapter execution roles ────────────────────────────────────────────

data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "adapter_invoke_agentcore" {
  statement {
    sid       = "InvokeAgentCoreRuntime"
    actions   = ["bedrock-agentcore:InvokeAgentRuntime"]
    resources = ["arn:aws:bedrock-agentcore:${var.aws_region}:${data.aws_caller_identity.current.account_id}:runtime/*"]
  }
}

resource "aws_iam_role" "investigator_adapter" {
  name               = "incident-agent-investigator-adapter-${var.env}"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_role_policy_attachment" "investigator_adapter_basic" {
  role       = aws_iam_role.investigator_adapter.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "investigator_adapter_agentcore" {
  name   = "invoke-agentcore"
  role   = aws_iam_role.investigator_adapter.id
  policy = data.aws_iam_policy_document.adapter_invoke_agentcore.json
}

resource "aws_iam_role" "remediation_adapter" {
  name               = "incident-agent-remediation-adapter-${var.env}"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_role_policy_attachment" "remediation_adapter_basic" {
  role       = aws_iam_role.remediation_adapter.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "remediation_adapter_agentcore" {
  name   = "invoke-agentcore"
  role   = aws_iam_role.remediation_adapter.id
  policy = data.aws_iam_policy_document.adapter_invoke_agentcore.json
}

data "aws_iam_policy_document" "remediation_adapter_ssm" {
  statement {
    sid       = "ReadGithubRepoParam"
    actions   = ["ssm:GetParameter"]
    resources = ["arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/incident-agent/*"]
  }
}

resource "aws_iam_role_policy" "remediation_adapter_ssm" {
  name   = "ssm-read"
  role   = aws_iam_role.remediation_adapter.id
  policy = data.aws_iam_policy_document.remediation_adapter_ssm.json
}
