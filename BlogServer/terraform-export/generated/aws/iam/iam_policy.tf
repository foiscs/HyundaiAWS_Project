resource "aws_iam_policy" "tfer--CWLtoKinesisPolicy" {
  name = "CWLtoKinesisPolicy"
  path = "/"

  policy = <<POLICY
{
  "Statement": [
    {
      "Action": [
        "kinesis:PutRecord",
        "kinesis:PutRecords"
      ],
      "Effect": "Allow",
      "Resource": [
        "arn:aws:kinesis:ap-northeast-2:253157413163:stream/cloudtrail-stream",
        "arn:aws:kinesis:ap-northeast-2:253157413163:stream/security-hub-stream",
        "arn:aws:kinesis:ap-northeast-2:253157413163:stream/guardduty-stream"
      ]
    }
  ],
  "Version": "2012-10-17"
}
POLICY
}

resource "aws_iam_policy" "tfer--CloudTrail-CloudWatch-Logs-Policy" {
  name = "CloudTrail-CloudWatch-Logs-Policy"
  path = "/"

  policy = <<POLICY
{
  "Statement": [
    {
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams"
      ],
      "Effect": "Allow",
      "Resource": "arn:aws:logs:ap-northeast-2:123456789012:log-group:music1-app-cloudtrail-logs:*"
    }
  ],
  "Version": "2012-10-17"
}
POLICY
}

resource "aws_iam_policy" "tfer--Cloudtrail-CW-access-policy-test-cloudtrail-logs-52d5f29b-6727-451a-9308-3bda693dd917" {
  description = "Policy for config CloudWathLogs for trail test-cloudtrail-logs, created by CloudTrail console"
  name        = "Cloudtrail-CW-access-policy-test-cloudtrail-logs-52d5f29b-6727-451a-9308-3bda693dd917"
  path        = "/service-role/"

  policy = <<POLICY
{
  "Statement": [
    {
      "Action": [
        "logs:CreateLogStream"
      ],
      "Effect": "Allow",
      "Resource": [
        "arn:aws:logs:ap-northeast-2:253157413163:log-group:aws-cloudtrail-logs:log-stream:253157413163_CloudTrail_ap-northeast-2*"
      ],
      "Sid": "AWSCloudTrailCreateLogStream2014110"
    },
    {
      "Action": [
        "logs:PutLogEvents"
      ],
      "Effect": "Allow",
      "Resource": [
        "arn:aws:logs:ap-northeast-2:253157413163:log-group:aws-cloudtrail-logs:log-stream:253157413163_CloudTrail_ap-northeast-2*"
      ],
      "Sid": "AWSCloudTrailPutLogEvents20141101"
    }
  ],
  "Version": "2012-10-17"
}
POLICY
}

resource "aws_iam_policy" "tfer--CustomEKSClusterolicy" {
  name = "CustomEKSClusterolicy"
  path = "/"

  policy = <<POLICY
{
  "Statement": [
    {
      "Action": [
        "eks:DescribeCluster",
        "eks:ListClusters",
        "eks:DescribeNodegroup",
        "eks:ListNodegroups",
        "eks:DescribeFargateProfile",
        "eks:ListFargateProfiles"
      ],
      "Effect": "Allow",
      "Resource": "*"
    }
  ],
  "Version": "2012-10-17"
}
POLICY
}

resource "aws_iam_policy" "tfer--ECS_FARGATE" {
  name = "ECS_FARGATE"
  path = "/"

  policy = <<POLICY
{
  "Statement": [
    {
      "Action": [
        "ecs:*",
        "iam:PassRole",
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogGroups"
      ],
      "Effect": "Allow",
      "Resource": "*"
    }
  ],
  "Version": "2012-10-17"
}
POLICY
}

resource "aws_iam_policy" "tfer--SimpleBlogS3Policy" {
  description = "SimpleBlogS3Policy"
  name        = "SimpleBlogS3Policy"
  path        = "/"

  policy = <<POLICY
{
  "Statement": [
    {
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:PutObjectAcl"
      ],
      "Effect": "Allow",
      "Resource": "arn:aws:s3:::test-simpleblog-files/*",
      "Sid": "SimpleBlogS3Access"
    },
    {
      "Action": [
        "s3:ListBucket"
      ],
      "Effect": "Allow",
      "Resource": "arn:aws:s3:::test-simpleblog-files",
      "Sid": "SimpleBlogS3List"
    }
  ],
  "Version": "2012-10-17"
}
POLICY
}

resource "aws_iam_policy" "tfer--SplunkAdminMinimumPolicy" {
  description = "SplunkAdminMinimumPolicy"
  name        = "SplunkAdminMinimumPolicy"
  path        = "/"

  policy = <<POLICY
{
  "Statement": [
    {
      "Action": [
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:GetRole",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:PutRolePolicy",
        "iam:DeleteRolePolicy",
        "iam:PassRole",
        "iam:ListRoles",
        "iam:TagRole",
        "iam:UntagRole",
        "iam:UpdateAssumeRolePolicy"
      ],
      "Effect": "Allow",
      "Resource": "*"
    }
  ],
  "Version": "2012-10-17"
}
POLICY
}
