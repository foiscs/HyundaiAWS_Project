resource "aws_cloudwatch_event_target" "tfer--AutoScalingManagedRule-002F-autoscaling" {
  arn           = "arn:aws:autoscaling:ap-northeast-2:::"
  force_destroy = "false"
  rule          = "AutoScalingManagedRule"
  target_id     = "autoscaling"
}

resource "aws_cloudwatch_event_target" "tfer--EKSComputeManagedRule-002F-EKSComputeManagedRule" {
  arn           = "arn:aws:eks-compute:ap-northeast-2:::"
  force_destroy = "false"
  rule          = "EKSComputeManagedRule"
  target_id     = "EKSComputeManagedRule"
}

resource "aws_cloudwatch_event_target" "tfer--guardduty-to-cloudwatch-rule-002F-1" {
  arn           = "arn:aws:logs:ap-northeast-2:253157413163:log-group:aws-guardduty-logs"
  force_destroy = "false"
  rule          = "guardduty-to-cloudwatch-rule"
  target_id     = "1"
}

resource "aws_cloudwatch_event_target" "tfer--security-hub-to-cloudwatch-rule-002F-1" {
  arn           = "arn:aws:logs:ap-northeast-2:253157413163:log-group:security-hub-findings"
  force_destroy = "false"
  rule          = "security-hub-to-cloudwatch-rule"
  target_id     = "1"
}
