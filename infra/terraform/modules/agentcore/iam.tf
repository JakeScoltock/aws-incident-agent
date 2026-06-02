data "aws_iam_policy_document" "agentcore_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["bedrock.amazonaws.com"]
    }
  }
}

# ── Investigator agent ────────────────────────────────────────────────────────
# Needs: Bedrock (model invocation), CloudWatch (metrics + logs), DynamoDB (read)

resource "aws_iam_role" "investigator" {
  name               = "incident-agent-investigator-${var.env}"
  assume_role_policy = data.aws_iam_policy_document.agentcore_assume.json
}

data "aws_iam_policy_document" "investigator" {
  statement {
    sid       = "Bedrock"
    actions   = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
    resources = ["*"]
  }

  statement {
    sid = "CloudWatch"
    actions = [
      "cloudwatch:GetMetricStatistics",
      "cloudwatch:GetMetricData",
      "logs:StartQuery",
      "logs:GetQueryResults",
      "logs:StopQuery",
      "logs:DescribeLogGroups",
    ]
    resources = ["*"]
  }

  statement {
    sid       = "DynamoDBRead"
    actions   = ["dynamodb:Query", "dynamodb:GetItem"]
    resources = [var.deployment_history_table_arn]
  }
}

resource "aws_iam_role_policy" "investigator" {
  name   = "investigator-policy"
  role   = aws_iam_role.investigator.id
  policy = data.aws_iam_policy_document.investigator.json
}

# ── Remediation agent ─────────────────────────────────────────────────────────
# Needs: Bedrock (model invocation), SSM (read GitHub token) — no AWS write access

resource "aws_iam_role" "remediation" {
  name               = "incident-agent-remediation-${var.env}"
  assume_role_policy = data.aws_iam_policy_document.agentcore_assume.json
}

data "aws_iam_policy_document" "remediation" {
  statement {
    sid       = "Bedrock"
    actions   = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
    resources = ["*"]
  }

  statement {
    sid     = "SSMReadSecrets"
    actions = ["ssm:GetParameter"]
    resources = [
      aws_ssm_parameter.github_token.arn,
      aws_ssm_parameter.github_repo.arn,
    ]
  }

  statement {
    sid       = "KMSDecryptSSM"
    actions   = ["kms:Decrypt"]
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["ssm.${var.aws_region}.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy" "remediation" {
  name   = "remediation-policy"
  role   = aws_iam_role.remediation.id
  policy = data.aws_iam_policy_document.remediation.json
}
