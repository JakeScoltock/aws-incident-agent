locals {
  investigator_runtime_name = "incident_agent_investigator_${var.env}"
  remediation_runtime_name  = "incident_agent_remediation_${var.env}"
  manage_script             = "${path.root}/../../scripts/manage_runtimes.py"
}

# null_resource used because the Terraform AWS provider does not yet have a
# native aws_bedrockagentcore_runtime resource. Re-runs whenever the image
# tag, role, or ECR URL changes — keeping the runtime in sync with ECR.

resource "null_resource" "investigator_runtime" {
  triggers = {
    image_tag = var.image_tag
    role_arn  = aws_iam_role.investigator.arn
    ecr_url   = aws_ecr_repository.investigator.repository_url
  }

  provisioner "local-exec" {
    command = "python3 ${local.manage_script}"
    environment = {
      RUNTIME_NAME = local.investigator_runtime_name
      IMAGE_URI    = "${aws_ecr_repository.investigator.repository_url}:${var.image_tag}"
      ROLE_ARN     = aws_iam_role.investigator.arn
      AWS_REGION   = var.aws_region
    }
  }
}

resource "null_resource" "remediation_runtime" {
  triggers = {
    image_tag = var.image_tag
    role_arn  = aws_iam_role.remediation.arn
    ecr_url   = aws_ecr_repository.remediation.repository_url
  }

  provisioner "local-exec" {
    command = "python3 ${local.manage_script}"
    environment = {
      RUNTIME_NAME = local.remediation_runtime_name
      IMAGE_URI    = "${aws_ecr_repository.remediation.repository_url}:${var.image_tag}"
      ROLE_ARN     = aws_iam_role.remediation.arn
      AWS_REGION   = var.aws_region
    }
  }
}
