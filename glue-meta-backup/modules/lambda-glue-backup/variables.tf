### modules/lambda-glue-backup/variables.tf

variable "function_name" {
  description = "Name of the Lambda function"
  type        = string
}

variable "backup_bucket_arn" {
  description = "ARN of the backup S3 bucket"
  type        = string
}

variable "backup_bucket_name" {
  description = "Name of the backup S3 bucket"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "lambda_timeout" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 900
}

variable "lambda_memory" {
  description = "Lambda memory in MB"
  type        = number
  default     = 512
}
