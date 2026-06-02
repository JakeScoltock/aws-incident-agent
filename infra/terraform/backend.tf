terraform {
  required_version = ">= 1.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }

  # Remote state — create the bucket and lock table before uncommenting:
  #   aws s3 mb s3://aws-incident-agent-tfstate --region eu-west-1
  #   aws dynamodb create-table \
  #     --table-name aws-incident-agent-tfstate-lock \
  #     --attribute-definitions AttributeName=LockID,AttributeType=S \
  #     --key-schema AttributeName=LockID,KeyType=HASH \
  #     --billing-mode PAY_PER_REQUEST \
  #     --region eu-west-1
  #
  # backend "s3" {
  #   bucket         = "aws-incident-agent-tfstate"
  #   key            = "incident-agent/terraform.tfstate"
  #   region         = "eu-west-1"
  #   dynamodb_table = "aws-incident-agent-tfstate-lock"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project = "aws-incident-agent"
      Env     = var.env
    }
  }
}
