resource "aws_cloudwatch_event_rule" "tfer--AutoScalingManagedRule" {
  description    = "This rule is used to route Instance notifications to EC2 Auto Scaling"
  event_bus_name = "default"
  event_pattern  = "{\"detail-type\":[\"EC2 Instance Rebalance Recommendation\",\"EC2 Spot Instance Interruption Warning\"],\"source\":[\"aws.ec2\"]}"
  force_destroy  = "false"
  is_enabled     = "true"
  name           = "AutoScalingManagedRule"
  state          = "ENABLED"
}

resource "aws_cloudwatch_event_rule" "tfer--EKSComputeManagedRule" {
  description    = "EKSComputeManagedRule"
  event_bus_name = "default"
  event_pattern  = "{\"account\":[\"253157413163\"],\"detail-type\":[\"EC2 Spot Instance Interruption Warning\",\"EC2 Instance State-change Notification\",\"EC2 Instance Rebalance Recommendation\",\"AWS Health Event\"],\"source\":[\"aws.ec2\",\"aws.health\"]}"
  force_destroy  = "false"
  is_enabled     = "true"
  name           = "EKSComputeManagedRule"
  state          = "ENABLED"
}

resource "aws_cloudwatch_event_rule" "tfer--guardduty-all-events" {
  event_bus_name = "default"
  event_pattern  = "{\"source\":[\"aws.guardduty\"]}"
  force_destroy  = "false"
  is_enabled     = "true"
  name           = "guardduty-all-events"
  state          = "ENABLED"
}

resource "aws_cloudwatch_event_rule" "tfer--guardduty-to-cloudwatch-rule" {
  event_bus_name = "default"
  event_pattern  = "{\"detail-type\":[\"GuardDuty Finding\"],\"source\":[\"aws.guardduty\"]}"
  force_destroy  = "false"
  is_enabled     = "true"
  name           = "guardduty-to-cloudwatch-rule"
  state          = "ENABLED"
}

resource "aws_cloudwatch_event_rule" "tfer--security-hub-to-cloudwatch-rule" {
  event_bus_name = "default"
  event_pattern  = "{\"detail-type\":[\"Security Hub Findings - Imported\"],\"source\":[\"aws.securityhub\"]}"
  force_destroy  = "false"
  is_enabled     = "true"
  name           = "security-hub-to-cloudwatch-rule"
  state          = "ENABLED"
}
