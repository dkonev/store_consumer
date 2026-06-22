### modules/eventbridge/variables.tf

variable "schedule_name" {
  description = "Name of the EventBridge schedule"
  type        = string
}

variable "schedule_expression" {
  description = "Schedule expression for EventBridge rule"
  type        = string
}

variable "glue_lambda_arn" {
  description = "ARN of the Glue backup Lambda function"
  type        = string
}

variable "glue_lambda_function_name" {
  description = "Name of the Glue backup Lambda function"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}
