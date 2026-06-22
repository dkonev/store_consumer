### modules/lambda-glue-restore/outputs.tf

output "lambda_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.glue_restore.arn
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.glue_restore.function_name
}

output "lambda_role_arn" {
  description = "ARN of the Lambda IAM role"
  value       = aws_iam_role.lambda.arn
}