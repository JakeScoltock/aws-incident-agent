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
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }

  # Bootstrap (one-time, before first terraform init):
  #   aws s3 mb s3://aws-incident-agent-tfstate --region eu-west-1

  # Region must be hardcoded here — backend blocks don't support variable interpolation.
  backend "s3" {
    bucket         = "aws-incident-agent-tfstate"
    key            = "incident-agent/terraform.tfstate"
    region         = "eu-west-1"
    use_lockfile = true
    encrypt        = true
  }
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
