resource "aws_iam_instance_profile" "tfer--EC2CloudWatchRule" {
  name = "EC2CloudWatchRule"
  path = "/"
  role = "EC2CloudWatchRule"
}

resource "aws_iam_instance_profile" "tfer--SimpleBlogEC2Role" {
  name = "SimpleBlogEC2Role"
  path = "/"
  role = "SimpleBlogEC2Role"
}

resource "aws_iam_instance_profile" "tfer--ec2-ecr-full-access" {
  name = "ec2-ecr-full-access"
  path = "/"
  role = "ec2-ecr-full-access"
}
