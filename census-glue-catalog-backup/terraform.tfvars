### terraform.tfvars

aws_region          = "us-gov-west-1"
environment         = "dev"
project_name        = "glue-backup"
backup_bucket_name  = "glue-meta-backup"
enable_versioning   = true
retention_days      = 30
backup_schedule     = "cron(0 3 * * ? *)"  # 3 AM UTC daily
lambda_timeout      = 900
lambda_memory       = 512
