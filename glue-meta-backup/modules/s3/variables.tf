### modules/s3/variables.tf

variable "bucket_name" {
  description = "Name of the S3 backup bucket"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "enable_versioning" {
  description = "Enable bucket versioning"
  type        = bool
  default     = true
}

variable "retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 30
}
