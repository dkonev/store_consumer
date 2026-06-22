### modules/lambda-glue-backup/main.tf

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "${var.function_name}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

#########
resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.function_name}-glue-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "glue:GetDatabase",
          "glue:GetDatabases",
          "glue:GetTable",
          "glue:GetTables",
          "glue:GetPartition",
          "glue:GetPartitions",
          "glue:GetCrawler",
          "glue:GetCrawlers",
          "glue:GetJob",
          "glue:GetJobs",
          "glue:GetClassifier",
          "glue:GetClassifiers",
          "glue:GetConnection",
          "glue:GetConnections",
          "glue:GetDevEndpoint",
          "glue:GetDevEndpoints",
          "glue:GetTrigger",
          "glue:GetTriggers",
          "glue:GetWorkflow",
          "glue:ListWorkflows",
          "glue:GetSecurityConfiguration",
          "glue:GetSecurityConfigurations",
          "glue:GetCatalogImportStatus",
          "glue:SearchTables"
        ]
        Resource = [
          "arn:aws-us-gov:glue:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:catalog",
          "arn:aws-us-gov:glue:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:database/*",
          "arn:aws-us-gov:glue:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:table/*/*",
          "arn:aws-us-gov:glue:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:crawler/*",
          "arn:aws-us-gov:glue:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:job/*",
          "arn:aws-us-gov:glue:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:trigger/*",
          "arn:aws-us-gov:glue:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:workflow/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "glue:GetDatabases",
          "glue:GetTables"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:PutObjectAcl",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          var.backup_bucket_arn,
          "${var.backup_bucket_arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws-us-gov:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.function_name}:*"
      }
    ]
  })
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda_log_group" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = 14
}

# Lambda Function Package
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/lambda/glue_backup.py"
  output_path = "${path.module}/lambda/glue_backup.zip"
}

# Lambda Function
resource "aws_lambda_function" "glue_backup" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = var.function_name
  role            = aws_iam_role.lambda_role.arn
  handler         = "glue_backup.lambda_handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime         = "python3.11"
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory

  environment {
    variables = {
      BACKUP_BUCKET = var.backup_bucket_name
      ENVIRONMENT   = var.environment
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda_log_group,
    aws_iam_role_policy.lambda_policy
  ]
}
