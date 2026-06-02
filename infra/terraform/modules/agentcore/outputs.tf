output "investigator_ecr_url" {
  value = aws_ecr_repository.investigator.repository_url
}

output "remediation_ecr_url" {
  value = aws_ecr_repository.remediation.repository_url
}

output "investigator_role_arn" {
  value = aws_iam_role.investigator.arn
}

output "remediation_role_arn" {
  value = aws_iam_role.remediation.arn
}

output "github_token_ssm_name" {
  value = aws_ssm_parameter.github_token.name
}
