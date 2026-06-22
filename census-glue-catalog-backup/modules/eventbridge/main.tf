### modules/eventbridge/main.tf

# EventBridge Rule for scheduled backup
resource "aws_cloudwatch_event_rule" "backup_schedule" {
  name                = var.schedule_name
  description         = "Schedule for backing up Glue Catalog"
  schedule_expression = var.schedule_expression
}

# EventBridge Target for Glue Lambda
resource "aws_cloudwatch_event_target" "glue_lambda" {
  rule      = aws_cloudwatch_event_rule.backup_schedule.name
  target_id = "GlueBackupLambda"
  arn       = var.glue_lambda_arn
}

# Lambda permission for EventBridge (Glue Lambda)
resource "aws_lambda_permission" "allow_eventbridge_glue" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = var.glue_lambda_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.backup_schedule.arn
}
