### outputs.tf

output "backup_bucket_name" {
  description = "Name of the backup S3 bucket"
  value       = module.s3_backup.bucket_name
}

output "backup_bucket_arn" {
  description = "ARN of the backup S3 bucket"
  value       = module.s3_backup.bucket_arn
}

output "glue_backup_lambda_arn" {
  description = "ARN of the Glue backup Lambda function"
  value       = module.lambda_glue_backup.lambda_arn
}

#output "glue_restore_lambda_arn" {
#  description = "ARN of the Glue restore Lambda function"
#  value       = module.lambda_glue_restore.lambda_function_arn
#}

output "eventbridge_rule_arn" {
  description = "ARN of the EventBridge rule"
  value       = module.eventbridge_schedule.rule_arn
}
