# ========================================
# Users
# ========================================
output "blog_s3_user_status" {
  description = "Status of blog-s3-user (existing or created)"
  value = try(data.external.blog_s3_user_existing.result["user_name"], null) != null ? "existing" : "created"
}
output "blog_s3_user_name" {
  description = "Blog S3 user name"
  value = try(data.external.blog_s3_user_existing.result["user_name"], aws_iam_user.blog_s3_user[0].name)
}
output "blog_s3_user_arn" {
  description = "Blog S3 user ARN"
  value = try(data.external.blog_s3_user_existing.result["arn"], aws_iam_user.blog_s3_user[0].arn)
}
output "splunk_kinesis_reader_status" {
  description = "Status of splunk-kinesis-reader (existing or created)"
  value = try(data.external.splunk_kinesis_reader_existing.result["user_name"], null) != null ? "existing" : "created"
}
output "splunk_kinesis_reader_name" {
  description = "Splunk Kinesis reader user name"
  value = try(data.external.splunk_kinesis_reader_existing.result["user_name"], aws_iam_user.splunk_kinesis_reader[0].name)
}
output "splunk_kinesis_reader_arn" {
  description = "Splunk Kinesis reader user ARN"
  value = try(data.external.splunk_kinesis_reader_existing.result["arn"], aws_iam_user.splunk_kinesis_reader[0].arn)
}

# ========================================
# Roles
# ========================================
output "cloudtrail_cloudwatch_role_status" {
  description = "Status of CloudTrail CloudWatch role (existing or created)"
  value = try(data.external.cloudtrail_cloudwatch_existing.result["role_name"], null) != null ? "existing" : "created"       
}
output "cloudtrail_cloudwatch_role_name" {
  description = "CloudTrail CloudWatch role name"
  value = try(data.external.cloudtrail_cloudwatch_existing.result["role_name"], aws_iam_role.cloudtrail_cloudwatch[0].name)
}
output "cloudtrail_cloudwatch_role_arn" {
  description = "CloudTrail CloudWatch role ARN"
  value = try(data.external.cloudtrail_cloudwatch_existing.result["arn"], aws_iam_role.cloudtrail_cloudwatch[0].arn)
}
output "cloudwatch_kinesis_role_status" {
  description = "Status of CloudWatch Kinesis role (existing or created)"
  value = try(data.external.cloudwatch_kinesis_existing.result["role_name"], null) != null ? "existing" : "created"
}
output "cloudwatch_kinesis_role_name" {
  description = "CloudWatch Kinesis role name"
  value = try(data.external.cloudwatch_kinesis_existing.result["role_name"], aws_iam_role.cloudwatch_kinesis[0].name)        
}
output "cloudwatch_kinesis_role_arn" {
  description = "CloudWatch Kinesis role ARN"
  value = try(data.external.cloudwatch_kinesis_existing.result["arn"], aws_iam_role.cloudwatch_kinesis[0].arn)
}
output "firehose_waf_role_status" {
  description = "Status of Firehose WAF role (existing or created)"
  value = try(data.external.firehose_waf_role_existing.result["role_name"], null) != null ? "existing" : "created"
}
output "firehose_role_name" {
  description = "Firehose WAF role name"
  value = try(data.external.firehose_waf_role_existing.result["role_name"], aws_iam_role.firehose_waf_role[0].name)
}
output "firehose_role_arn" {
  description = "Firehose WAF role ARN"
  value = try(data.external.firehose_waf_role_existing.result["arn"], aws_iam_role.firehose_waf_role[0].arn)
}

# ========================================
# Policies
# ========================================
output "blog_s3_policy_status" {
  description = "Status of blog S3 policy (existing or created)"
  value = try(data.external.blog_s3_policy_existing.result["policy_name"], null) != null ? "existing" : "created"
}
output "blog_s3_policy_arn" {
  description = "Blog S3 policy ARN"
  value = try(data.external.blog_s3_policy_existing.result["policy_arn"], aws_iam_policy.blog_s3_policy[0].arn)
}
output "splunk_kinesis_policy_status" {
  description = "Status of Splunk Kinesis policy (existing or created)"
  value = try(data.external.splunk_kinesis_policy_existing.result["policy_name"], null) != null ? "existing" : "created"     
}
output "splunk_kinesis_policy_arn" {
  description = "Splunk Kinesis policy ARN"
  value = try(data.external.splunk_kinesis_policy_existing.result["policy_arn"], aws_iam_policy.splunk_kinesis_policy[0].arn)
}
output "cloudtrail_cloudwatch_policy_status" {
  description = "Status of CloudTrail CloudWatch policy (existing or created)"
  value = try(data.external.cloudtrail_cloudwatch_policy_existing.result["policy_name"], null) != null ? "existing" : "created"
}
output "cloudtrail_cloudwatch_policy_arn" {
  description = "CloudTrail CloudWatch policy ARN"
  value = try(data.external.cloudtrail_cloudwatch_policy_existing.result["policy_arn"], aws_iam_policy.cloudtrail_cloudwatch_policy[0].arn)
}
output "cloudwatch_kinesis_policy_status" {
  description = "Status of CloudWatch Kinesis policy (existing or created)"
  value = try(data.external.cloudwatch_kinesis_policy_existing.result["policy_name"], null) != null ? "existing" : "created"
}
output "cloudwatch_kinesis_policy_arn" {
  description = "CloudWatch Kinesis policy ARN"
  value = try(data.external.cloudwatch_kinesis_policy_existing.result["policy_arn"], aws_iam_policy.cloudwatch_kinesis_policy[0].arn)
}
output "firehose_waf_policy_status" {
  description = "Status of Firehose WAF policy (existing or created)"
  value = try(data.external.firehose_waf_policy_existing.result["policy_name"], null) != null ? "existing" : "created"       
}
output "firehose_waf_policy_arn" {
  description = "Firehose WAF policy ARN"
  value = try(data.external.firehose_waf_policy_existing.result["policy_arn"], aws_iam_policy.firehose_waf_policy[0].arn)
}

# ========================================
# Access Keys (if created)
# ========================================
output "blog_s3_user_access_key_id" {
  description = "Blog S3 user access key ID (if created)"
  value = var.create_access_keys && data.external.blog_s3_user_existing.result["exists"] == "false" ? aws_iam_access_key.blog_s3_user[0].id : null
  sensitive = true
}
output "splunk_kinesis_reader_access_key_id" {
  description = "Splunk Kinesis reader access key ID (if created)"
  value = var.create_access_keys && data.external.splunk_kinesis_reader_existing.result["exists"] == "false" ? aws_iam_access_key.splunk_kinesis_reader[0].id : null
  sensitive = true
}

# ========================================
# Secret Manager ARNs (if created)
# ========================================
output "blog_s3_credentials_secret_arn" {
  description = "Blog S3 user credentials secret ARN"
  value = var.create_access_keys && data.external.blog_s3_user_existing.result["exists"] == "false" ? aws_secretsmanager_secret.blog_s3_user_credentials[0].arn : null
}
output "splunk_kinesis_credentials_secret_arn" {
  description = "Splunk Kinesis reader credentials secret ARN"  
  value = var.create_access_keys && data.external.splunk_kinesis_reader_existing.result["exists"] == "false" ? aws_secretsmanager_secret.splunk_kinesis_reader_credentials[0].arn : null
}