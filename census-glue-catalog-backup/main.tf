### main.tf

terraform {
  required_version = ">= 1.0"
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
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = var.environment
      Project     = var.project_name
      ManagedBy   = "Terraform"
      Purpose     = "GlueBackup"
    }
  }
}


# S3 Backup Bucket Module
module "s3_backup" {
  source = "./modules/s3"

  bucket_name       = var.backup_bucket_name
  environment       = var.environment
  enable_versioning = var.enable_versioning
  retention_days    = var.retention_days
}

# Lambda for Glue Backup Module
module "lambda_glue_backup" {
  source = "./modules/lambda-glue-backup"

  function_name     = "${var.project_name}-glue-backup-${var.environment}"
  backup_bucket_arn = module.s3_backup.bucket_arn
  backup_bucket_name = module.s3_backup.bucket_name
  environment       = var.environment
  lambda_timeout    = var.lambda_timeout
  lambda_memory     = var.lambda_memory
}

# Lambda Glue Restore Module
#module "lambda_glue_restore" {
#  source = "./modules/lambda-glue-restore"
#
#  function_name       = "${var.environment}-glue-restore"
#  environment         = var.environment
#  backup_bucket_name  = module.s3_backup.bucket_name
#  iam_role_arn        = module.iam_roles.glue_restore_lambda_role_arn
#  lambda_timeout      = var.lambda_timeout
#  lambda_memory_size  = var.lambda_memory_size
#}


# EventBridge Schedule Module
module "eventbridge_schedule" {
  source = "./modules/eventbridge"

  schedule_name                 = "${var.project_name}-backup-schedule-${var.environment}"
  schedule_expression           = var.backup_schedule
  glue_lambda_arn              = module.lambda_glue_backup.lambda_arn
  glue_lambda_function_name    = module.lambda_glue_backup.lambda_function_name
  environment                  = var.environment
}
