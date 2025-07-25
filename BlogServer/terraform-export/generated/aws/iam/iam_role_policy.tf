resource "aws_iam_role_policy" "tfer--AmazonEKSAutoNodeRole_eks-nodegroup-s3-access-policy" {
  name = "eks-nodegroup-s3-access-policy"

  policy = <<POLICY
{
  "Statement": [
    {
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Effect": "Allow",
      "Resource": [
        "arn:aws:s3:::test-simpleblog-files",
        "arn:aws:s3:::test-simpleblog-files/*"
      ]
    }
  ],
  "Version": "2012-10-17"
}
POLICY

  role = "AmazonEKSAutoNodeRole"
}
