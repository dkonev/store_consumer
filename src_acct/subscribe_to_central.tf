locals {
  log_groups = [
    "/aws/lambda/test-lambda",
    "vpcflowlogs"
  ]
}

resource "aws_cloudwatch_log_subscription_filter" "to_central" {
  for_each = toset(local.log_groups)
  name            = "subscribe-${replace(each.value, "/", "-")}"
  log_group_name  = each.value
  filter_pattern  = ""
  destination_arn = "arn:aws-us-gov:logs:us-gov-west-1:${var.central_account_id}:destination:central-log-destination"
  #depends_on = [aws_cloudwatch_log_destination_policy.central]
}
