output "aws_cloudwatch_dashboard_tfer--music-app-dash_id" {
  value = "${aws_cloudwatch_dashboard.tfer--music-app-dash.id}"
}

output "aws_cloudwatch_event_rule_tfer--AutoScalingManagedRule_id" {
  value = "${aws_cloudwatch_event_rule.tfer--AutoScalingManagedRule.id}"
}

output "aws_cloudwatch_event_rule_tfer--EKSComputeManagedRule_id" {
  value = "${aws_cloudwatch_event_rule.tfer--EKSComputeManagedRule.id}"
}

output "aws_cloudwatch_event_rule_tfer--guardduty-all-events_id" {
  value = "${aws_cloudwatch_event_rule.tfer--guardduty-all-events.id}"
}

output "aws_cloudwatch_event_rule_tfer--guardduty-to-cloudwatch-rule_id" {
  value = "${aws_cloudwatch_event_rule.tfer--guardduty-to-cloudwatch-rule.id}"
}

output "aws_cloudwatch_event_rule_tfer--security-hub-to-cloudwatch-rule_id" {
  value = "${aws_cloudwatch_event_rule.tfer--security-hub-to-cloudwatch-rule.id}"
}

output "aws_cloudwatch_event_target_tfer--AutoScalingManagedRule-002F-autoscaling_id" {
  value = "${aws_cloudwatch_event_target.tfer--AutoScalingManagedRule-002F-autoscaling.id}"
}

output "aws_cloudwatch_event_target_tfer--EKSComputeManagedRule-002F-EKSComputeManagedRule_id" {
  value = "${aws_cloudwatch_event_target.tfer--EKSComputeManagedRule-002F-EKSComputeManagedRule.id}"
}

output "aws_cloudwatch_event_target_tfer--guardduty-to-cloudwatch-rule-002F-1_id" {
  value = "${aws_cloudwatch_event_target.tfer--guardduty-to-cloudwatch-rule-002F-1.id}"
}

output "aws_cloudwatch_event_target_tfer--security-hub-to-cloudwatch-rule-002F-1_id" {
  value = "${aws_cloudwatch_event_target.tfer--security-hub-to-cloudwatch-rule-002F-1.id}"
}
