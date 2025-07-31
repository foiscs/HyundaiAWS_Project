# Get current AWS account ID and region
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Check if blog-s3-user already exists
data "aws_iam_user" "blog_s3_user_existing" {
  user_name = "blog-s3-user"
}

# Check if splunk-kinesis-reader already exists  
data "aws_iam_user" "splunk_kinesis_reader_existing" {
  user_name = "splunk-kinesis-reader"
}

# Create blog-s3-user if it doesn't exist
resource "aws_iam_user" "blog_s3_user" {
  count = try(data.aws_iam_user.blog_s3_user_existing.user_name, null) == null ? 1 : 0
  name  = "blog-s3-user"
  
  tags = merge(var.common_tags, {
    Name      = "blog-s3-user"
    Component = "Security"
    Purpose   = "S3 access for blog application"
    Type      = "ServiceAccount"
  })
}

# Create splunk-kinesis-reader if it doesn't exist
resource "aws_iam_user" "splunk_kinesis_reader" {
  count = try(data.aws_iam_user.splunk_kinesis_reader_existing.user_name, null) == null ? 1 : 0
  name  = "splunk-kinesis-reader"
  
  tags = merge(var.common_tags, {
    Name      = "splunk-kinesis-reader"
    Component = "Security"
    Purpose   = "Kinesis data reading for Splunk"
    Type      = "ServiceAccount"
  })
}

# Check if blog_s3_policy already exists
data "aws_iam_policy" "blog_s3_policy_existing" {
    name = "blog-s3-user-policy"
}
# S3 access policy for blog-s3-user
resource "aws_iam_policy" "blog_s3_policy" {
  count       = try(data.aws_iam_policy.blog_s3_policy_existing.name, null) == null ? 1 : 0
  name        = "blog-s3-user-policy"
  description = "S3 access policy for blog application"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:ListAllMyBuckets",
          "s3:PutObjectAcl"
        ]
        Resource = [
          "arn:aws:s3:::${var.s3_logs_bucket_name}",
          "arn:aws:s3:::${var.s3_logs_bucket_name}/*"
        ]
      }
    ]
  })
  
  tags = var.common_tags
}

# Check if splunk_kinesis_policy already exists
data "aws_iam_policy" "splunk_kinesis_policy_existing" {
    name = "splunk-kinesis-reader-policy"
}
# Kinesis read policy for splunk-kinesis-reader
resource "aws_iam_policy" "splunk_kinesis_policy" {
  count       = try(data.aws_iam_policy.splunk_kinesis_policy_existing.name, null) == null ? 1 : 0
  name        = "splunk-kinesis-reader-policy"
  description = "Kinesis read access policy for Splunk"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "kinesis:DescribeStream",
          "kinesis:GetShardIterator",
          "kinesis:GetRecords",
          "kinesis:ListStreams",
          "kinesis:ListShards",
        ]
        Resource = [
          "arn:aws:kinesis:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:stream/cloudtrail-stream",
          "arn:aws:kinesis:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:stream/security-hub-stream",
          "arn:aws:kinesis:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:stream/guardduty-stream"
        ]
      },
      {
        Effect = "Allow",
        Action = [
            "dynamodb:CreateTable",
            "dynamodb:GetItem",
            "dynamodb:PutItem",
            "dynamodb:UpdateItem",
            "dynamodb:DeleteItem",
            "dynamodb:Scan",
            "dynamodb:Query"
        ],
        Resource = "arn:aws:dynamodb:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:table/splunk_checkpoints"
      }
    ]
  })
  
  tags = var.common_tags
}

# Attach S3 policy to blog-s3-user
resource "aws_iam_user_policy_attachment" "blog_s3_user_policy" {
    user       = try(data.aws_iam_user.blog_s3_user_existing.user_name, aws_iam_user.blog_s3_user[0].name)
    policy_arn = try(data.aws_iam_policy.blog_s3_policy_existing.arn, aws_iam_policy.blog_s3_policy[0].arn)
}

# Attach Kinesis policy to splunk-kinesis-reader
resource "aws_iam_user_policy_attachment" "splunk_kinesis_reader_policy" {
    user       = try(data.aws_iam_user.splunk_kinesis_reader_existing.user_name, aws_iam_user.splunk_kinesis_reader[0].name)
    policy_arn = try(data.aws_iam_policy.splunk_kinesis_policy_existing.arn, aws_iam_policy.splunk_kinesis_policy[0].arn)
}

# Optional: Create access keys for the users
resource "aws_iam_access_key" "blog_s3_user" {
  count = var.create_access_keys && try(data.aws_iam_user.blog_s3_user_existing.user_name, null) == null ? 1 : 0
  user  = aws_iam_user.blog_s3_user[0].name
}

resource "aws_iam_access_key" "splunk_kinesis_reader" {
  count = var.create_access_keys && try(data.aws_iam_user.splunk_kinesis_reader_existing.user_name, null) == null ? 1 : 0
  user  = aws_iam_user.splunk_kinesis_reader[0].name
}

# Store credentials in Secrets Manager (optional, for security)
resource "aws_secretsmanager_secret" "blog_s3_user_credentials" {
  count       = var.create_access_keys && try(data.aws_iam_user.blog_s3_user_existing.user_name, null) == null ? 1 : 0
  name        = "${var.project_name}/blog/s3-logs-user-credentials"
  description = "Blog S3 Logs User Access Credentials"
  
  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-blog-s3-user-credentials"
    Component = "Security"
    Purpose   = "Credentials Storage"
  })
}

resource "aws_secretsmanager_secret_version" "blog_s3_user_credentials" {
  count     = var.create_access_keys && try(data.aws_iam_user.blog_s3_user_existing.user_name, null) == null ? 1 : 0
  secret_id = aws_secretsmanager_secret.blog_s3_user_credentials[0].id
  secret_string = jsonencode({
    access_key_id     = aws_iam_access_key.blog_s3_user[0].id
    secret_access_key = aws_iam_access_key.blog_s3_user[0].secret
    user_name         = aws_iam_user.blog_s3_user[0].name
  })
}

resource "aws_secretsmanager_secret" "splunk_kinesis_reader_credentials" {
  count       = var.create_access_keys && try(data.aws_iam_user.splunk_kinesis_reader_existing.user_name, null) == null ? 1 : 0
  name        = "${var.project_name}/splunk/kinesis-reader-credentials"
  description = "Splunk Kinesis Reader Access Credentials"
  
  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-splunk-kinesis-reader-credentials"
    Component = "Security"
    Purpose   = "Credentials Storage"
  })
}

resource "aws_secretsmanager_secret_version" "splunk_kinesis_reader_credentials" {
  count     = var.create_access_keys && try(data.aws_iam_user.splunk_kinesis_reader_existing.user_name, null) == null ? 1 : 0
  secret_id = aws_secretsmanager_secret.splunk_kinesis_reader_credentials[0].id
  secret_string = jsonencode({
    access_key_id     = aws_iam_access_key.splunk_kinesis_reader[0].id
    secret_access_key = aws_iam_access_key.splunk_kinesis_reader[0].secret
    user_name         = aws_iam_user.splunk_kinesis_reader[0].name
  })
}


# CloudTrail -> CloudWatch Role section
data "aws_iam_role" "cloudtrail_cloudwatch_existing" {
  name = "CloudTrail-CloutWatchLogs-Role"
}
# Create CloudTrail to CloudWatch role if it doesn't exist
resource "aws_iam_role" "cloudtrail_cloudwatch" {
  count = try(data.aws_iam_role.cloudtrail_cloudwatch_existing.name, null) == null ? 1 : 0
  name  = "CloudTrail-CloutWatchLogs-Role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action = "sts:AssumeRole"
        Condition = {
          StringEquals = {
            "aws:SourceArn" = "arn:aws:cloudtrail:${data.aws_region.current.name}:${data.aws_caller_identity.     
                                          current.account_id}:trail/${var.project_name}-cloudtrail"
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })
  tags = merge(var.common_tags, {
    Name      = "CloudTrail_CloudWatchLogs_Role"
    Component = "Security"
    Service   = "CloudTrail"
  })
}

# Check if cloudtrail_cloudwatch_policy already exists
data "aws_iam_policy" "cloudtrail_cloudwatch_policy_existing" {
  name = "CloudTrail-CloudWatchLogs-Policy"
}
# CloudTrail to CloudWatch Logs Policy
resource "aws_iam_policy" "cloudtrail_cloudwatch_policy" {
  count       = try(data.aws_iam_policy.cloudtrail_cloudwatch_policy_existing.name, null) == null ? 1 : 0
  name        = "CloudTrail-CloudWatchLogs-Policy"
  description = "CloudTrail에서 CloudWatch Logs로 전송하는 정책"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AWSCloudTrailCreateLogStream"
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream"
        ]
        Resource = [
          "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:${var.project_name}-cloudtrail-logs:log-stream:${data.aws_caller_identity.current.account_id}_CloudTrail_${data.aws_region.current.name}*"
        ]
      },
      {
        Sid    = "AWSCloudTrailPutLogEvents"
        Effect = "Allow"
        Action = [
          "logs:PutLogEvents"
        ]
        Resource = [
          "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:${var.project_name}-cloudtrail-logs:log-stream:${data.aws_caller_identity.current.account_id}_CloudTrail_${data.aws_region.current.name}*"
        ]
      }
    ]
  })
  tags = var.common_tags
}
# Attach CloudTrail to CloudWatch Logs Policy to role
resource "aws_iam_role_policy_attachment" "cloudtrail_cloudwatch" {
  role       = try(data.aws_iam_role.cloudtrail_cloudwatch_existing.name, aws_iam_role.cloudtrail_cloudwatch[0].name)
  policy_arn = try(data.aws_iam_policy.cloudtrail_cloudwatch_policy_existing.arn, aws_iam_policy.cloudtrail_cloudwatch_policy[0].arn)
}

#CloudWatch -> Kinesis Role section
data "aws_iam_role" "cloudwatch_kinesis_existing" {
  name = "CloutWatchLogs-Kinesis-Role"
}
# Create CloudWatch to Kinesis role if it doesn't exist
resource "aws_iam_role" "cloudwatch_kinesis" {
  count = try(data.aws_iam_role.cloudwatch_kinesis_existing.name, null) == null ? 1 : 0
  name  = "CloutWatchLogs-Kinesis-Role"
  assume_role_policy = jsonencode(
    {
        Version: "2012-10-17",
        Statement: [
            {
                Effect: "Allow",
                Principal: {
                    Service: "logs.amazonaws.com"
                },
                Action: "sts:AssumeRole"
            }
        ]
    })
  tags = merge(var.common_tags, {
    Name      = "CloutWatchLogs-Kinesis-Role"
    Component = "Security"
    Service   = "CloudWatch"
  })
}

# Check if cloudwatch_kinesis_policy already exists
data "aws_iam_policy" "cloudwatch_kinesis_policy_existing" {
  name = "CloudWatchLogs-Kinesis-Policy"
}
# CloudWatch Logs to Kinesis Policy
resource "aws_iam_policy" "cloudwatch_kinesis_policy" {
  count       = try(data.aws_iam_policy.cloudwatch_kinesis_policy_existing.name, null) == null ? 1 : 0
  name        = "CloudWatchLogs-Kinesis-Policy"
  description = "CloudWatch Logs에서 Kinesis로 전송하는 정책"
  policy = jsonencode({
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "kinesis:PutRecord",
                "kinesis:PutRecords"
            ],
            "Resource": [
                "arn:aws:kinesis:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:stream/cloudtrail-stream",
                "arn:aws:kinesis:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:stream/security-hub-stream",
                "arn:aws:kinesis:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:stream/guardduty-stream"
            ]
        }
    ]
  })
  tags = var.common_tags
}
# Attach CloudWatch Logs to Kinesis Policy to role
resource "aws_iam_role_policy_attachment" "cloudwatch_kinesis" {
  role       = try(data.aws_iam_role.cloudwatch_kinesis_existing.name, aws_iam_role.cloudwatch_kinesis[0].name)
  policy_arn = try(data.aws_iam_policy.cloudwatch_kinesis_policy_existing.arn, aws_iam_policy.cloudwatch_kinesis_policy[0].arn)
}

# Check if firehose_waf_role already exists
data "aws_iam_role" "firehose_waf_role_existing" {
  name = "${var.project_name}-firehose-waf-role"
}
# Firehose Role for WAF logs
resource "aws_iam_role" "firehose_waf_role" {
  count = try(data.aws_iam_role.firehose_waf_role_existing.name, null) == null ? 1 : 0
  name = "${var.project_name}-firehose-waf-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "firehose.amazonaws.com"
        }
      }
    ]
  })
  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-firehose-waf-role"
    Component = "Security"
    Service   = "Firehose"
  })
}
# Check if firehose_waf_policy already exists
data "aws_iam_policy" "firehose_waf_policy_existing" {
  name = "${var.project_name}-firehose-waf-policy"
}
# Firehose Policy for S3 delivery
resource "aws_iam_policy" "firehose_waf_policy" {
  count = try(data.aws_iam_policy.firehose_waf_policy_existing.name, null) == null ? 1 : 0
  name        = "${var.project_name}-firehose-waf-policy"
  description = "Policy for Firehose to deliver WAF logs to S3"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:AbortMultipartUpload",
          "s3:GetBucketLocation",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:ListBucketMultipartUploads",
          "s3:PutObject"
        ]
        Resource = [
          "arn:aws:s3:::${var.s3_logs_bucket_name}",
          "arn:aws:s3:::${var.s3_logs_bucket_name}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:PutLogEvents"
        ]
        Resource = [
          "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/kinesisfirehose/*"
        ]
      }
    ]
  })
  tags = var.common_tags
}

resource "aws_iam_role_policy_attachment" "firehose_waf" {
    role       = try(data.aws_iam_role.firehose_waf_role_existing.name, aws_iam_role.firehose_waf_role[0].name)     
    policy_arn = try(data.aws_iam_policy.firehose_waf_policy_existing.arn, aws_iam_policy.firehose_waf_policy[0].arn)
}