resource "aws_iam_role_policy_attachment" "tfer--AWSReservedSSO_ec2-dav_4cd2effaee51ed53_AmazonEC2FullAccess" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2FullAccess"
  role       = "AWSReservedSSO_ec2-dav_4cd2effaee51ed53"
}

resource "aws_iam_role_policy_attachment" "tfer--AWSServiceRoleForAmazonEKSNodegroup_AWSServiceRoleForAmazonEKSNodegroup" {
  policy_arn = "arn:aws:iam::aws:policy/aws-service-role/AWSServiceRoleForAmazonEKSNodegroup"
  role       = "AWSServiceRoleForAmazonEKSNodegroup"
}

resource "aws_iam_role_policy_attachment" "tfer--AWSServiceRoleForAmazonEKS_AmazonEKSServiceRolePolicy" {
  policy_arn = "arn:aws:iam::aws:policy/aws-service-role/AmazonEKSServiceRolePolicy"
  role       = "AWSServiceRoleForAmazonEKS"
}

resource "aws_iam_role_policy_attachment" "tfer--AWSServiceRoleForAmazonGuardDutyMalwareProtection_AmazonGuardDutyMalwareProtectionServiceRolePolicy" {
  policy_arn = "arn:aws:iam::aws:policy/aws-service-role/AmazonGuardDutyMalwareProtectionServiceRolePolicy"
  role       = "AWSServiceRoleForAmazonGuardDutyMalwareProtection"
}

resource "aws_iam_role_policy_attachment" "tfer--AWSServiceRoleForAmazonGuardDuty_AmazonGuardDutyServiceRolePolicy" {
  policy_arn = "arn:aws:iam::aws:policy/aws-service-role/AmazonGuardDutyServiceRolePolicy"
  role       = "AWSServiceRoleForAmazonGuardDuty"
}

resource "aws_iam_role_policy_attachment" "tfer--AWSServiceRoleForAutoScaling_AutoScalingServiceRolePolicy" {
  policy_arn = "arn:aws:iam::aws:policy/aws-service-role/AutoScalingServiceRolePolicy"
  role       = "AWSServiceRoleForAutoScaling"
}

resource "aws_iam_role_policy_attachment" "tfer--AWSServiceRoleForCloudTrail_CloudTrailServiceRolePolicy" {
  policy_arn = "arn:aws:iam::aws:policy/aws-service-role/CloudTrailServiceRolePolicy"
  role       = "AWSServiceRoleForCloudTrail"
}

resource "aws_iam_role_policy_attachment" "tfer--AWSServiceRoleForECS_AmazonECSServiceRolePolicy" {
  policy_arn = "arn:aws:iam::aws:policy/aws-service-role/AmazonECSServiceRolePolicy"
  role       = "AWSServiceRoleForECS"
}

resource "aws_iam_role_policy_attachment" "tfer--AWSServiceRoleForElasticLoadBalancing_AWSElasticLoadBalancingServiceRolePolicy" {
  policy_arn = "arn:aws:iam::aws:policy/aws-service-role/AWSElasticLoadBalancingServiceRolePolicy"
  role       = "AWSServiceRoleForElasticLoadBalancing"
}

resource "aws_iam_role_policy_attachment" "tfer--AWSServiceRoleForGlobalAccelerator_AWSGlobalAcceleratorSLRPolicy" {
  policy_arn = "arn:aws:iam::aws:policy/aws-service-role/AWSGlobalAcceleratorSLRPolicy"
  role       = "AWSServiceRoleForGlobalAccelerator"
}

resource "aws_iam_role_policy_attachment" "tfer--AWSServiceRoleForOrganizations_AWSOrganizationsServiceTrustPolicy" {
  policy_arn = "arn:aws:iam::aws:policy/aws-service-role/AWSOrganizationsServiceTrustPolicy"
  role       = "AWSServiceRoleForOrganizations"
}

resource "aws_iam_role_policy_attachment" "tfer--AWSServiceRoleForRDS_AmazonRDSServiceRolePolicy" {
  policy_arn = "arn:aws:iam::aws:policy/aws-service-role/AmazonRDSServiceRolePolicy"
  role       = "AWSServiceRoleForRDS"
}

resource "aws_iam_role_policy_attachment" "tfer--AWSServiceRoleForSSO_AWSSSOServiceRolePolicy" {
  policy_arn = "arn:aws:iam::aws:policy/aws-service-role/AWSSSOServiceRolePolicy"
  role       = "AWSServiceRoleForSSO"
}

resource "aws_iam_role_policy_attachment" "tfer--AWSServiceRoleForSecurityHub_AWSSecurityHubServiceRolePolicy" {
  policy_arn = "arn:aws:iam::aws:policy/aws-service-role/AWSSecurityHubServiceRolePolicy"
  role       = "AWSServiceRoleForSecurityHub"
}

resource "aws_iam_role_policy_attachment" "tfer--AWSServiceRoleForSupport_AWSSupportServiceRolePolicy" {
  policy_arn = "arn:aws:iam::aws:policy/aws-service-role/AWSSupportServiceRolePolicy"
  role       = "AWSServiceRoleForSupport"
}

resource "aws_iam_role_policy_attachment" "tfer--AWSServiceRoleForTrustedAdvisor_AWSTrustedAdvisorServiceRolePolicy" {
  policy_arn = "arn:aws:iam::aws:policy/aws-service-role/AWSTrustedAdvisorServiceRolePolicy"
  role       = "AWSServiceRoleForTrustedAdvisor"
}

resource "aws_iam_role_policy_attachment" "tfer--AmazonEKSAutoClusterRole_AmazonEKSBlockStoragePolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSBlockStoragePolicy"
  role       = "AmazonEKSAutoClusterRole"
}

resource "aws_iam_role_policy_attachment" "tfer--AmazonEKSAutoClusterRole_AmazonEKSClusterPolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = "AmazonEKSAutoClusterRole"
}

resource "aws_iam_role_policy_attachment" "tfer--AmazonEKSAutoClusterRole_AmazonEKSComputePolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSComputePolicy"
  role       = "AmazonEKSAutoClusterRole"
}

resource "aws_iam_role_policy_attachment" "tfer--AmazonEKSAutoClusterRole_AmazonEKSLoadBalancingPolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSLoadBalancingPolicy"
  role       = "AmazonEKSAutoClusterRole"
}

resource "aws_iam_role_policy_attachment" "tfer--AmazonEKSAutoClusterRole_AmazonEKSNetworkingPolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSNetworkingPolicy"
  role       = "AmazonEKSAutoClusterRole"
}

resource "aws_iam_role_policy_attachment" "tfer--AmazonEKSAutoNodeRole_AmazonEC2ContainerRegistryReadOnly" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = "AmazonEKSAutoNodeRole"
}

resource "aws_iam_role_policy_attachment" "tfer--AmazonEKSAutoNodeRole_AmazonEKSWorkerNodePolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = "AmazonEKSAutoNodeRole"
}

resource "aws_iam_role_policy_attachment" "tfer--CWLtoKinesisRole_CWLtoKinesisPolicy" {
  policy_arn = "arn:aws:iam::253157413163:policy/CWLtoKinesisPolicy"
  role       = "CWLtoKinesisRole"
}

resource "aws_iam_role_policy_attachment" "tfer--CloudTrail_CloudWatchLogs_Role_Cloudtrail-CW-access-policy-test-cloudtrail-logs-52d5f29b-6727-451a-9308-3bda693dd917" {
  policy_arn = "arn:aws:iam::253157413163:policy/service-role/Cloudtrail-CW-access-policy-test-cloudtrail-logs-52d5f29b-6727-451a-9308-3bda693dd917"
  role       = "CloudTrail_CloudWatchLogs_Role"
}

resource "aws_iam_role_policy_attachment" "tfer--CloudtrailRole_CloudTrail-CloudWatch-Logs-Policy" {
  policy_arn = "arn:aws:iam::253157413163:policy/CloudTrail-CloudWatch-Logs-Policy"
  role       = "CloudtrailRole"
}

resource "aws_iam_role_policy_attachment" "tfer--EC2CloudWatchRule_CloudWatchAgentServerPolicy" {
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
  role       = "EC2CloudWatchRule"
}

resource "aws_iam_role_policy_attachment" "tfer--SimpleBlogEC2Role_AmazonEC2ContainerRegistryPowerUser" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser"
  role       = "SimpleBlogEC2Role"
}

resource "aws_iam_role_policy_attachment" "tfer--SimpleBlogEC2Role_SimpleBlogS3Policy" {
  policy_arn = "arn:aws:iam::253157413163:policy/SimpleBlogS3Policy"
  role       = "SimpleBlogEC2Role"
}

resource "aws_iam_role_policy_attachment" "tfer--ec2-ecr-full-access_AmazonEC2ContainerRegistryFullAccess" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess"
  role       = "ec2-ecr-full-access"
}

resource "aws_iam_role_policy_attachment" "tfer--rds-monitoring-role_AmazonRDSEnhancedMonitoringRole" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
  role       = "rds-monitoring-role"
}
