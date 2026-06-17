resource "aws_cloudwatch_log_group" "sfn" {
  name              = "/aws/states/incident-agent-${var.env}"
  retention_in_days = 14
}

resource "aws_sfn_state_machine" "incident_pipeline" {
  name     = "incident-agent-${var.env}"
  role_arn = aws_iam_role.sfn.arn
  type     = "STANDARD"

  definition = jsonencode({
    Comment = "AWS Incident Agent — investigate alarm then open a remediation PR"
    StartAt = "ExtractAlarmContext"

    States = {
      ExtractAlarmContext = {
        Type = "Pass"
        Parameters = {
          "alarm_name.$"   = "$.detail.alarmName"
          "alarm_state.$"  = "$.detail.state.value"
          "alarm_reason.$" = "$.detail.state.reason"
          "account_id.$"   = "$.account"
          "aws_region.$"   = "$.region"
          "triggered_at.$" = "$.time"
        }
        Next = "Investigate"
      }

      Investigate = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = aws_lambda_function.investigator_adapter.arn
          "Payload.$"  = "$"
        }
        ResultSelector = {
          "body.$" = "$.Payload.body"
        }
        ResultPath = "$.investigation"
        Retry = [{
          ErrorEquals     = ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException"]
          IntervalSeconds = 2
          MaxAttempts     = 2
          BackoffRate     = 2
        }]
        Catch = [{
          ErrorEquals = ["States.ALL"]
          Next        = "NotifyFailure"
          ResultPath  = "$.error"
        }]
        Next = "CheckConfidence"
      }

      CheckConfidence = {
        Type = "Choice"
        Choices = [{
          Variable                 = "$.investigation.body.confidence"
          NumericGreaterThanEquals = 0.5
          Next                     = "Remediate"
        }]
        Default = "NotifyLowConfidence"
      }

      Remediate = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = aws_lambda_function.remediation_adapter.arn
          "Payload.$"  = "$"
        }
        ResultSelector = {
          "body.$" = "$.Payload.body"
        }
        ResultPath = "$.remediation"
        Retry = [{
          ErrorEquals     = ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException"]
          IntervalSeconds = 2
          MaxAttempts     = 2
          BackoffRate     = 2
        }]
        Catch = [{
          ErrorEquals = ["States.ALL"]
          Next        = "NotifyFailure"
          ResultPath  = "$.error"
        }]
        Next = "NotifySuccess"
      }

      NotifySuccess = {
        Type     = "Task"
        Resource = "arn:aws:states:::sns:publish"
        Parameters = {
          TopicArn    = var.alert_topic_arn
          "Message.$" = "States.Format('Incident resolved: {}. PR: {}', $.investigation.body.root_cause_summary, $.remediation.body.pr_url)"
          Subject     = "Incident Agent — Remediation PR opened"
        }
        Catch = [{
          ErrorEquals = ["States.ALL"]
          Next        = "Fail"
          ResultPath  = "$.notifyError"
        }]
        Next = "Succeed"
      }

      NotifyLowConfidence = {
        Type     = "Task"
        Resource = "arn:aws:states:::sns:publish"
        Parameters = {
          TopicArn    = var.alert_topic_arn
          "Message.$" = "States.Format('Low-confidence investigation ({}). Manual review required. Alarm: {}', $.investigation.body.confidence, $.alarm_name)"
          Subject     = "Incident Agent — Low confidence, manual review needed"
        }
        Catch = [{
          ErrorEquals = ["States.ALL"]
          Next        = "Fail"
          ResultPath  = "$.notifyError"
        }]
        Next = "Succeed"
      }

      NotifyFailure = {
        Type     = "Task"
        Resource = "arn:aws:states:::sns:publish"
        Parameters = {
          TopicArn    = var.alert_topic_arn
          "Message.$" = "States.Format('Incident agent failed. Alarm: {}. Error: {}', $.alarm_name, $.error.Cause)"
          Subject     = "Incident Agent — Pipeline failure"
        }
        Catch = [{
          ErrorEquals = ["States.ALL"]
          Next        = "Fail"
          ResultPath  = "$.notifyError"
        }]
        Next = "Fail"
      }

      Succeed = {
        Type = "Succeed"
      }

      Fail = {
        Type  = "Fail"
        Cause = "Incident pipeline failed — see SNS notification for details"
      }
    }
  })

  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.sfn.arn}:*"
    include_execution_data = true
    level                  = "ERROR"
  }
}
