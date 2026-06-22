# Create this in EACH source account
resource "aws_iam_role" "terraform_role" {
  name = "TerraformRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = {
        # Trust the CENTRAL account
        AWS = "arn:aws-us-gov:iam::${var.central_account_id}:root"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "terraform_role_policy" {
  name = "TerraformRolePolicy"
  role = aws_iam_role.terraform_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "logs:PutSubscriptionFilter",
        "logs:DeleteSubscriptionFilter",
        "logs:DescribeLogGroups",
        "logs:DescribeSubscriptionFilters"
      ]
      Resource = [
        "arn:aws-us-gov:logs:us-gov-west-1:${local.account_id}:log-group:*",
        "arn:aws-us-gov:logs:us-gov-west-1:${local.account_id}:destination:*"
      ]
    }]
  })
}
