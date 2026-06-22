### modules/lambda-glue-restore/main.tf

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# IAM Role for Lambda
resource "aws_iam_role" "lambda" {
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

  tags = {
    Name        = "${var.function_name}-role"
    Environment = var.environment
  }
}

# IAM Policy for Glue Write Access
resource "aws_iam_role_policy" "glue_access" {
  name = "${var.function_name}-glue-policy"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "glue:CreateDatabase",
          "glue:UpdateDatabase",
          "glue:CreateTable",
          "glue:UpdateTable",
          "glue:CreatePartition",
          "glue:BatchCreatePartition",
          "glue:CreateCrawler",
          "glue:UpdateCrawler",
          "glue:CreateJob",
          "glue:UpdateJob",
          "glue:CreateClassifier",
          "glue:UpdateClassifier",
          "glue:CreateConnection",
          "glue:UpdateConnection",
          "glue:CreateTrigger",
          "glue:UpdateTrigger",
          "glue:CreateWorkflow",
          "glue:UpdateWorkflow",
          "glue:CreateSecurityConfiguration",
          "glue:GetDatabase",
          "glue:GetTable",
          "glue:GetPartition",
          "glue:GetCrawler",
          "glue:GetJob",
          "glue:GetClassifier",
          "glue:GetConnection",
          "glue:GetTrigger",
          "glue:GetWorkflow",
          "glue:GetSecurityConfiguration"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "iam:PassRole"
        ]
        Resource = "*"
        Condition = {
          StringLike = {
            "iam:PassedToService" = "glue.amazonaws.com"
          }
        }
      }
    ]
  })
}

# IAM Policy for S3 Access
resource "aws_iam_role_policy" "s3_access" {
  name = "${var.function_name}-s3-policy"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          var.backup_bucket_arn,
          "${var.backup_bucket_arn}/*"
        ]
      }
    ]
  })
}

# CloudWatch Logs Policy
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws-us-gov:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Package Lambda function
data "archive_file" "lambda" {
  type        = "zip"
  source_file = "${path.module}/lambda/glue_restore.py"
  output_path = "${path.module}/lambda/glue_restore.zip"
}

# Lambda Function
resource "aws_lambda_function" "glue_restore" {
  filename         = data.archive_file.lambda.output_path
  function_name    = var.function_name
  role            = aws_iam_role.lambda.arn
  handler         = "glue_restore.lambda_handler"
  source_code_hash = data.archive_file.lambda.output_base64sha256
  runtime         = "python3.11"
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory

  environment {
    variables = {
      BACKUP_BUCKET = var.backup_bucket_id
      ENVIRONMENT   = var.environment
    }
  }

  tags = {
    Name        = var.function_name
    Environment = var.environment
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = 14

  tags = {
    Name        = var.function_name
    Environment = var.environment
  }
}
