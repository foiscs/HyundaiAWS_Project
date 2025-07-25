resource "aws_iam_group" "tfer--Administer" {
  name = "Administer"
  path = "/"
}

resource "aws_iam_group" "tfer--PowerUsers" {
  name = "PowerUsers"
  path = "/"
}

resource "aws_iam_group" "tfer--ServiceUserGroup" {
  name = "ServiceUserGroup"
  path = "/"
}

resource "aws_iam_group" "tfer--SplunkAdmin" {
  name = "SplunkAdmin"
  path = "/"
}
