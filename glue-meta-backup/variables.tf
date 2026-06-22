### variables.tf

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-gov-west-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "glue-backup"
}

variable "backup_bucket_name" {
  description = "Name of the S3 backup bucket"
  type        = string
}

variable "enable_versioning" {
  description = "Enable S3 bucket versioning"
  type        = bool
  default     = true
}

variable "retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 30
}

variable "backup_schedule" {
  description = "EventBridge schedule expression for backups (10 PM daily)"
  type        = string
  default     = "cron(0 22 * * ? *)"
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 900
}

variable "lambda_memory" {
  description = "Lambda function memory in MB"
  type        = number
  default     = 512
}
