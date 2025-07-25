resource "aws_iam_user_group_membership" "tfer--20010304h-002F-PowerUsers" {
  groups = ["PowerUsers"]
  user   = "20010304h"
}

resource "aws_iam_user_group_membership" "tfer--admin-002F-Administer" {
  groups = ["Administer"]
  user   = "admin"
}

resource "aws_iam_user_group_membership" "tfer--admin-002F-SplunkAdmin" {
  groups = ["SplunkAdmin"]
  user   = "admin"
}

resource "aws_iam_user_group_membership" "tfer--blog-s3-user-002F-ServiceUserGroup" {
  groups = ["ServiceUserGroup"]
  user   = "blog-s3-user"
}

resource "aws_iam_user_group_membership" "tfer--godori1012-002F-PowerUsers" {
  groups = ["PowerUsers"]
  user   = "godori1012"
}

resource "aws_iam_user_group_membership" "tfer--godori1012-002F-SplunkAdmin" {
  groups = ["SplunkAdmin"]
  user   = "godori1012"
}

resource "aws_iam_user_group_membership" "tfer--hako5460-002F-PowerUsers" {
  groups = ["PowerUsers"]
  user   = "hako5460"
}

resource "aws_iam_user_group_membership" "tfer--splunk-kinesis-reader-002F-ServiceUserGroup" {
  groups = ["ServiceUserGroup"]
  user   = "splunk-kinesis-reader"
}

resource "aws_iam_user_group_membership" "tfer--test_user-002F-Administer" {
  groups = ["Administer"]
  user   = "test_user"
}

resource "aws_iam_user_group_membership" "tfer--xogoon-002F-PowerUsers" {
  groups = ["PowerUsers"]
  user   = "xogoon"
}
