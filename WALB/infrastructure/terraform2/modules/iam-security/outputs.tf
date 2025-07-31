output "cloudtrail_cloudwatch_role_arn" {
  description = "ARN of CloudTrail to CloudWatch role"
  value       = try(data.aws_iam_role.cloudtrail_cloudwatch_existing.arn, aws_iam_role.cloudtrail_cloudwatch[0].arn)
}
output "cloudwatch_kinesis_role_arn" {
  description = "ARN of CloudWatch to Kinesis role"
  value       = try(data.aws_iam_role.cloudwatch_kinesis_existing.arn, aws_iam_role.cloudwatch_kinesis[0].arn)
}
output "firehose_role_arn" {
  description = "ARN of Firehose IAM role"
  value       = aws_iam_role.firehose_waf_role.arn
}