resource "aws_iam_user_policy_attachment" "tfer--20010304h_IAMUserChangePassword" {
  policy_arn = "arn:aws:iam::aws:policy/IAMUserChangePassword"
  user       = "20010304h"
}

resource "aws_iam_user_policy_attachment" "tfer--admin_IAMUserChangePassword" {
  policy_arn = "arn:aws:iam::aws:policy/IAMUserChangePassword"
  user       = "admin"
}

resource "aws_iam_user_policy_attachment" "tfer--blog-s3-user_SimpleBlogS3Policy" {
  policy_arn = "arn:aws:iam::253157413163:policy/SimpleBlogS3Policy"
  user       = "blog-s3-user"
}

resource "aws_iam_user_policy_attachment" "tfer--github-actions-deploy-user_AdministratorAccess" {
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
  user       = "github-actions-deploy-user"
}

resource "aws_iam_user_policy_attachment" "tfer--github-actions-deploy-user_AmazonEC2ContainerRegistryFullAccess" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess"
  user       = "github-actions-deploy-user"
}

resource "aws_iam_user_policy_attachment" "tfer--github-actions-deploy-user_AmazonEKSClusterPolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  user       = "github-actions-deploy-user"
}

resource "aws_iam_user_policy_attachment" "tfer--github-actions-deploy-user_AmazonEKSWorkerNodePolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  user       = "github-actions-deploy-user"
}

resource "aws_iam_user_policy_attachment" "tfer--godori1012_IAMUserChangePassword" {
  policy_arn = "arn:aws:iam::aws:policy/IAMUserChangePassword"
  user       = "godori1012"
}

resource "aws_iam_user_policy_attachment" "tfer--hako5460_IAMUserChangePassword" {
  policy_arn = "arn:aws:iam::aws:policy/IAMUserChangePassword"
  user       = "hako5460"
}

resource "aws_iam_user_policy_attachment" "tfer--k8s_AmazonEC2ContainerRegistryFullAccess" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess"
  user       = "k8s"
}

resource "aws_iam_user_policy_attachment" "tfer--k8s_AmazonEKSServicePolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSServicePolicy"
  user       = "k8s"
}

resource "aws_iam_user_policy_attachment" "tfer--k8s_AmazonEKSVPCResourceController" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSVPCResourceController"
  user       = "k8s"
}

resource "aws_iam_user_policy_attachment" "tfer--k8s_AmazonEKSWorkerNodePolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  user       = "k8s"
}

resource "aws_iam_user_policy_attachment" "tfer--k8s_AmazonEKS_CNI_Policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  user       = "k8s"
}

resource "aws_iam_user_policy_attachment" "tfer--k8s_ElasticLoadBalancingFullAccess" {
  policy_arn = "arn:aws:iam::aws:policy/ElasticLoadBalancingFullAccess"
  user       = "k8s"
}

resource "aws_iam_user_policy_attachment" "tfer--splunk-kinesis-reader_AmazonDynamoDBFullAccess" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
  user       = "splunk-kinesis-reader"
}

resource "aws_iam_user_policy_attachment" "tfer--splunk-kinesis-reader_AmazonKinesisReadOnlyAccess" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonKinesisReadOnlyAccess"
  user       = "splunk-kinesis-reader"
}

resource "aws_iam_user_policy_attachment" "tfer--splunk_addon_AmazonS3ReadOnlyAccess" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
  user       = "splunk_addon"
}

resource "aws_iam_user_policy_attachment" "tfer--xogoon_IAMUserChangePassword" {
  policy_arn = "arn:aws:iam::aws:policy/IAMUserChangePassword"
  user       = "xogoon"
}
