data "aws_region" "current" {}


# 기존 사용자 존재 여부 확인 (try 함수 사용)
data "aws_iam_user" "existing_users" {
  for_each = var.create_service_users ? toset([
    "splunkforwrder-kinesis-reader",
  ]) : toset([])
  
  user_name = each.value
  
  # 사용자가 존재하지 않아도 오류가 발생하지 않도록 처리
  lifecycle {
    postcondition {
      condition = can(self.user_name) ? true : var.skip_existing_users
      error_message = "User ${each.value} already exists. Set skip_existing_users=true to continue without creating this user."
    }
  }
}

#Role 생성
#CloudTrail -> CloutWatch Logs Role
resource "aws_iam_role" "cloudtrail_cloudwatch"{
    name = "CloudTrail-CloutWatchLogs-Role"

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
            "aws:SourceArn" = "arn:aws:cloudtrail:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:trail/${var.project_name}-cloudtrail"
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

#CloudTrail -> CloudWatch Logs Policy
resource "aws_iam_policy" "cloudtrail_cloudwatch_policy"{
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
#역할에 정책 연결
resource "aws_iam_role_policy_attachment" "cloudtrail_cloudwatch" {
  role       = aws_iam_role.cloudtrail_cloudwatch.name
  policy_arn = aws_iam_policy.cloudtrail_cloudwatch_policy.arn
}

#CloudWatch Logs → Kinesis IAM Role
resource "aws_iam_role" "cloudwatch_kinesis"{
  name = "CloudWatch_Kinesis"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "logs.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = merge(var.common_tags, {
    Name      = "CloudWatch_Kinesis"
    Component = "Security"
    Service   = "CloudWatch-Kinesis"
  })
}

# CloudWatch → Kinesis Policy
resource "aws_iam_policy" "cloudwatch_kinesis_policy" {
  name        = "CloudWatch_Kinesis_Policy"
  description = "CloudWatch Logs에서 Kinesis로 전송하는 정책"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "kinesis:PutRecord",
          "kinesis:PutRecords"
        ]
        Resource = [
            "arn:aws:kinesis:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:stream/cloudtrail-stream",
            "arn:aws:kinesis:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:stream/security-hub-stream", 
            "arn:aws:kinesis:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:stream/guardduty-stream"
        ]

      }
    ]
  })

  tags = var.common_tags
}

# CloudWatch → Kinesis 정책 연결
resource "aws_iam_role_policy_attachment" "cloudwatch_kinesis" {
  role       = aws_iam_role.cloudwatch_kinesis.name
  policy_arn = aws_iam_policy.cloudwatch_kinesis_policy.arn
}

# VPC Flow Logs → CloudWatch Role
resource "aws_iam_role" "vpc_flow_logs" {
  name = "${var.project_name}-vpc-flow-log-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "vpc-flow-logs.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-vpc-flow-log-role"
    Component = "Security"
    Service   = "VPC"
  })
}

# VPC Flow Logs Policy
resource "aws_iam_role_policy" "vpc_flow_logs_policy" {
  name = "${var.project_name}-vpc-flow-log-policy"
  role = aws_iam_role.vpc_flow_logs.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}


# Splunk forwarder에서 Kinesis 읽기 전용 계정
resource "aws_iam_user" "splunk_kinesis_reader" {
  count = var.create_service_users ? 1 : 0
  name  = "splunk-kinesis-reader"

  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-splunk-kinesis-reader"
    Component = "Security"
    Purpose   = "Kinesis Data Reading for Splunk"
    Type      = "ServiceAccount"
  })
}

# DynamoDB Full Access 정책 연결
resource "aws_iam_user_policy_attachment" "splunk_kinesis_reader_dynamodb" {
  count      = var.create_service_users ? 1 : 0
  user       = aws_iam_user.splunk_kinesis_reader[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
}
# Kinesis Read Only Access 정책 연결
resource "aws_iam_user_policy_attachment" "splunk_kinesis_reader_kinesis" {
  count      = var.create_service_users ? 1 : 0
  user       = aws_iam_user.splunk_kinesis_reader[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonKinesisReadOnlyAccess"
}

# Access Key 생성 (선택사항)
resource "aws_iam_access_key" "splunk_kinesis_reader" {
  count = var.create_service_users && var.create_access_keys ? 1 : 0
  user  = aws_iam_user.splunk_kinesis_reader[0].name
}

# Secrets Manager에 Access Key 저장 (보안 강화)
resource "aws_secretsmanager_secret" "splunk_kinesis_reader_credentials" {
  count       = var.create_service_users && var.create_access_keys ? 1 : 0
  name        = "${var.project_name}/splunk/kinesis-reader-credentials"
  description = "Splunk Kinesis Reader Access Credentials"

  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-splunk-kinesis-reader-credentials"
    Component = "Security"
    Purpose   = "Credentials Storage"
  })
}
resource "aws_secretsmanager_secret_version" "splunk_kinesis_reader_credentials" {
  count     = var.create_service_users && var.create_access_keys ? 1 : 0
  secret_id = aws_secretsmanager_secret.splunk_kinesis_reader_credentials[0].id
  secret_string = jsonencode({
    access_key_id     = aws_iam_access_key.splunk_kinesis_reader[0].id
    secret_access_key = aws_iam_access_key.splunk_kinesis_reader[0].secret
    user_name         = aws_iam_user.splunk_kinesis_reader[0].name
  })
}

resource "aws_iam_policy" "s3_logs_read_only" {
  name        = "${var.project_name}-s3-logs-read-only"
  description = "S3 로그 버킷 읽기 전용 정책"

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
          "arn:aws:s3:::${var.s3_bucket_name}",
          "arn:aws:s3:::${var.s3_bucket_name}/*"
        ]
      }
    ]
  })

  tags = var.common_tags
}