resource "aws_securityhub_standards_subscription" "tfer--arn-003A-aws-003A-securityhub-003A-ap-northeast-2-003A-253157413163-003A-subscription-002F-aws-foundational-security-best-practices-002F-v-002F-1-002E-0-002E-0" {
  depends_on    = ["aws_securityhub_account.tfer--253157413163"]
  standards_arn = "arn:aws:securityhub:ap-northeast-2::standards/aws-foundational-security-best-practices/v/1.0.0"
}

resource "aws_securityhub_standards_subscription" "tfer--arn-003A-aws-003A-securityhub-003A-ap-northeast-2-003A-253157413163-003A-subscription-002F-cis-aws-foundations-benchmark-002F-v-002F-1-002E-2-002E-0" {
  depends_on    = ["aws_securityhub_account.tfer--253157413163"]
  standards_arn = "arn:aws:securityhub:::ruleset/cis-aws-foundations-benchmark/v/1.2.0"
}
