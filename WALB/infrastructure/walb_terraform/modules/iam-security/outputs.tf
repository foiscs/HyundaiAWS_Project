# ========================================
# Users
# ========================================
output "blog_s3_user_name" {
  description = "Blog S3 user name"
  value       = aws_iam_user.blog_s3_user.name
}

output "blog_s3_user_arn" {
  description = "Blog S3 user ARN"
  value       = aws_iam_user.blog_s3_user.arn
}

output "splunk_kinesis_reader_name" {
  description = "Splunk Kinesis reader user name"
  value       = aws_iam_user.splunk_kinesis_reader.name
}

output "splunk_kinesis_reader_arn" {
  description = "Splunk Kinesis reader user ARN"
  value       = aws_iam_user.splunk_kinesis_reader.arn
}

# ========================================
# Roles
# ========================================
output "cloudtrail_cloudwatch_role_name" {
  description = "CloudTrail CloudWatch role name"
  value       = aws_iam_role.cloudtrail_cloudwatch.name
}

output "cloudtrail_cloudwatch_role_arn" {
  description = "CloudTrail CloudWatch role ARN"
  value       = aws_iam_role.cloudtrail_cloudwatch.arn
}

output "cloudwatch_kinesis_role_name" {
  description = "CloudWatch Kinesis role name"
  value       = aws_iam_role.cloudwatch_kinesis.name
}

output "cloudwatch_kinesis_role_arn" {
  description = "CloudWatch Kinesis role ARN"
  value       = aws_iam_role.cloudwatch_kinesis.arn
}

output "firehose_role_name" {
  description = "Firehose WAF role name"
  value       = aws_iam_role.firehose_waf_role.name
}

output "firehose_role_arn" {
  description = "Firehose WAF role ARN"
  value       = aws_iam_role.firehose_waf_role.arn
}

# ========================================
# Policies
# ========================================
output "blog_s3_policy_arn" {
  description = "Blog S3 policy ARN"
  value       = aws_iam_policy.blog_s3_policy.arn
}

output "splunk_kinesis_policy_arn" {
  description = "Splunk Kinesis policy ARN"
  value       = aws_iam_policy.splunk_kinesis_policy.arn
}

output "cloudtrail_cloudwatch_policy_arn" {
  description = "CloudTrail CloudWatch policy ARN"
  value       = aws_iam_policy.cloudtrail_cloudwatch_policy.arn
}

output "cloudwatch_kinesis_policy_arn" {
  description = "CloudWatch Kinesis policy ARN"
  value       = aws_iam_policy.cloudwatch_kinesis_policy.arn
}

output "firehose_waf_policy_arn" {
  description = "Firehose WAF policy ARN"
  value       = aws_iam_policy.firehose_waf_policy.arn
}

# ========================================
# Access Keys (if created)
# ========================================
output "blog_s3_user_access_key_id" {
  description = "Blog S3 user access key ID (if created)"
  value       = var.create_access_keys ? aws_iam_access_key.blog_s3_user[0].id : null
  sensitive   = true
}

output "splunk_kinesis_reader_access_key_id" {
  description = "Splunk Kinesis reader access key ID (if created)"
  value       = var.create_access_keys ? aws_iam_access_key.splunk_kinesis_reader[0].id : null
  sensitive   = true
}

# ========================================
# Secret Manager ARNs (if created)
# ========================================
output "blog_s3_credentials_secret_arn" {
  description = "Blog S3 user credentials secret ARN"
  value       = var.create_access_keys ? aws_secretsmanager_secret.blog_s3_user_credentials[0].arn : null
}

output "splunk_kinesis_credentials_secret_arn" {
  description = "Splunk Kinesis reader credentials secret ARN"
  value       = var.create_access_keys ? aws_secretsmanager_secret.splunk_kinesis_reader_credentials[0].arn : null
}