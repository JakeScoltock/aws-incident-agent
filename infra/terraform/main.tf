module "observability" {
  source = "./modules/observability"

  env         = var.env
  aws_region  = var.aws_region
  alert_email = var.alert_email
}

module "demo_api" {
  source = "./modules/demo_api"

  env                         = var.env
  aws_region                  = var.aws_region
  alarm_duration_threshold_ms = var.alarm_duration_threshold_ms
  alert_topic_arn             = module.observability.alert_topic_arn
}

module "agentcore" {
  source = "./modules/agentcore"

  env                           = var.env
  aws_region                    = var.aws_region
  deployment_history_table_arn  = module.observability.deployment_history_table_arn
  deployment_history_table_name = module.observability.deployment_history_table_name
  github_token                  = var.github_token
  github_repo                   = var.github_repo
  image_tag                     = var.image_tag
}

module "step_functions" {
  source = "./modules/step_functions"

  env             = var.env
  aws_region      = var.aws_region
  alert_topic_arn = module.observability.alert_topic_arn

  agentcore_investigator_role_arn   = module.agentcore.investigator_role_arn
  agentcore_remediation_role_arn    = module.agentcore.remediation_role_arn
  agentcore_investigator_ecr_url    = module.agentcore.investigator_ecr_url
  agentcore_remediation_ecr_url     = module.agentcore.remediation_ecr_url
  agentcore_investigator_runtime_id  = var.agentcore_investigator_runtime_id
  agentcore_remediation_runtime_id   = var.agentcore_remediation_runtime_id
  agentcore_investigator_runtime_arn = var.agentcore_investigator_runtime_arn
  agentcore_remediation_runtime_arn  = var.agentcore_remediation_runtime_arn
  monitored_function_name            = "incident-agent-demo-api-${var.env}"
  github_repo_ssm_name               = "/incident-agent/${var.env}/github-repo"
}

module "eventbridge" {
  source = "./modules/eventbridge"

  env               = var.env
  alarm_name_prefix = "incident-agent-${var.env}"
  state_machine_arn = module.step_functions.state_machine_arn
}
