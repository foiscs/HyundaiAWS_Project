resource "aws_iam_group_policy_attachment" "tfer--Administer_AdministratorAccess" {
  group      = "Administer"
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}

resource "aws_iam_group_policy_attachment" "tfer--PowerUsers_PowerUserAccess" {
  group      = "PowerUsers"
  policy_arn = "arn:aws:iam::aws:policy/PowerUserAccess"
}
