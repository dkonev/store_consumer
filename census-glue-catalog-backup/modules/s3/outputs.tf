### modules/s3/outputs.tf

output "bucket_name" {
  description = "Name of the backup bucket"
  value       = aws_s3_bucket.backup.id
}

output "bucket_arn" {
  description = "ARN of the backup bucket"
  value       = aws_s3_bucket.backup.arn
}

output "bucket_domain_name" {
  description = "Domain name of the backup bucket"
  value       = aws_s3_bucket.backup.bucket_domain_name
}
