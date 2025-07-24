# infrastructure/terraform/modules/eks/main.tf
# EKS 클러스터 구성을 위한 Terraform 모듈

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# KMS 키 (EKS 시크릿 암호화용)
resource "aws_kms_key" "eks" {
  description             = "EKS Secret Encryption Key - ${var.cluster_name}"
  deletion_window_in_days = var.kms_deletion_window
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow EKS to use the key"
        Effect = "Allow"
        Principal = {
          Service = "eks.amazonaws.com"
        }
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey"
        ]
        Resource = "*"
      },
      {
        Sid    = "Allow EC2 to use the key for EBS"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = [
          "kms:Decrypt",
          "kms:Encrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:CreateGrant",
          "kms:DescribeKey"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "kms:ViaService" = "ec2.${data.aws_region.current.name}.amazonaws.com"
          }
        }
      },
      {
        Sid    = "Allow autoscaling to use the key"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/aws-service-role/autoscaling.amazonaws.com/AWSServiceRoleForAutoScaling"
        }
        Action = [
          "kms:Decrypt",
          "kms:Encrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:CreateGrant",
          "kms:DescribeKey"
        ]
        Resource = "*"
      }
    ]
  })

  tags = merge(var.common_tags, {
    Name = "${var.cluster_name}-eks-kms-key"
    Use  = "EKS Secret Encryption"
  })
  lifecycle {
    ignore_changes = [tags_all]
  }
}

resource "aws_kms_alias" "eks" {
  name          = "alias/${var.cluster_name}-eks-test"
  target_key_id = aws_kms_key.eks.key_id

  lifecycle {
    create_before_destroy = true
  }
}

# 기존 데이터 소스를 try 함수로 감싸서 에러 방지
locals {
  log_group_name = "/aws/eks/${var.cluster_name}/cluster"
}

# CloudWatch 로그 그룹 생성 조건 수정
resource "aws_cloudwatch_log_group" "eks" {
  name              = local.log_group_name
  retention_in_days = var.log_retention_days

  tags = merge(var.common_tags, {
    Name = "${var.cluster_name}-eks-cluster-logs"
  })
  
  lifecycle {
    ignore_changes = [tags_all]
    create_before_destroy = true
    prevent_destroy = false
  }
}

# EKS 클러스터 서비스 역할
resource "aws_iam_role" "cluster" {
  name = "${var.cluster_name}-eks-cluster-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "eks.amazonaws.com"
        }
      }
    ]
  })

  tags = var.common_tags
  lifecycle {
    create_before_destroy = true
    prevent_destroy = false
  }
}

# EKS 클러스터 정책 연결
resource "aws_iam_role_policy_attachment" "cluster_AmazonEKSClusterPolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.cluster.name
}

resource "aws_iam_role_policy_attachment" "cluster_AmazonEKSVPCResourceController" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSVPCResourceController"
  role       = aws_iam_role.cluster.name
}

# EKS 클러스터 보안 그룹
resource "aws_security_group" "cluster" {
  name_prefix = "${var.cluster_name}-eks-cluster-"
  vpc_id      = var.vpc_id
  description = "Security group for EKS cluster control plane"

  # HTTPS 통신 (EKS API)
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = var.cluster_endpoint_private_access_cidrs
    description = "HTTPS access to EKS API"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = merge(var.common_tags, {
    Name = "${var.cluster_name}-eks-cluster-sg"
    Type = "EKS Cluster Security Group"
  })

  lifecycle {
    create_before_destroy = true
    ignore_changes = [tags_all]
  }
}

# EKS 클러스터
resource "aws_eks_cluster" "main" {
  name     = var.cluster_name
  role_arn = aws_iam_role.cluster.arn
  version  = var.cluster_version

  vpc_config {
    subnet_ids              = var.subnet_ids
    endpoint_private_access = var.cluster_endpoint_private_access
    endpoint_public_access  = var.cluster_endpoint_public_access
    public_access_cidrs     = var.cluster_endpoint_public_access_cidrs
    security_group_ids      = [aws_security_group.cluster.id]
  }

  # 제어 플레인 로깅 (ISMS-P 컴플라이언스)
  enabled_cluster_log_types = var.cluster_enabled_log_types

  # 시크릿 암호화 (ISMS-P 컴플라이언스)
  encryption_config {
    provider {
      key_arn = aws_kms_key.eks.arn
    }
    resources = ["secrets"]
  }

  tags = merge(var.common_tags, {
    Name = var.cluster_name
    Type = "EKS Cluster"
  })
  
  depends_on = [
    aws_iam_role_policy_attachment.cluster_AmazonEKSClusterPolicy,
    aws_iam_role_policy_attachment.cluster_AmazonEKSVPCResourceController,
    aws_cloudwatch_log_group.eks
  ]
}

# EKS 노드 그룹 IAM 역할
resource "aws_iam_role" "node_group" {
  name = "${var.cluster_name}-eks-node-group-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = ["ec2.amazonaws.com", "eks.amazonaws.com"]
        }
      }
    ]
  })

  tags = var.common_tags
  lifecycle {
    create_before_destroy = true
    prevent_destroy = false
  }

}

resource "aws_iam_role_policy_attachment" "ecr_pull" {
  role       = aws_iam_role.node_group.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

# EKS 노드 그룹 정책 연결
resource "aws_iam_role_policy_attachment" "node_group_AmazonEKSWorkerNodePolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.node_group.name
}

resource "aws_iam_role_policy_attachment" "node_group_AmazonEKS_CNI_Policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.node_group.name
}

resource "aws_iam_role_policy_attachment" "node_group_AmazonEC2ContainerRegistryReadOnly" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.node_group.name
}

# 추가 정책: CloudWatch 및 로깅
resource "aws_iam_role_policy_attachment" "node_group_CloudWatchAgentServerPolicy" {
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
  role       = aws_iam_role.node_group.name
}

# EKS 노드 그룹 보안 그룹
resource "aws_security_group" "node_group" {
  name_prefix = "${var.cluster_name}-eks-node-group-"
  vpc_id      = var.vpc_id
  description = "Security group for EKS node group"

  # 노드간 통신
  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    self        = true
    description = "Communication between nodes"
  }

  # SSH 접근 (선택사항)
  dynamic "ingress" {
    for_each = var.enable_ssh_access ? [1] : []
    content {
      from_port   = 22
      to_port     = 22
      protocol    = "tcp"
      cidr_blocks = var.ssh_access_cidrs
      description = "SSH access"
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = merge(var.common_tags, {
    Name = "${var.cluster_name}-eks-node-group-sg"
    Type = "EKS Node Group Security Group"
  })

  lifecycle {
    create_before_destroy = true
    ignore_changes = [tags_all]
  }
}

# 클러스터에서 노드 그룹으로 통신 허용
resource "aws_security_group_rule" "node_group_from_cluster" {
  type                     = "ingress"
  from_port               = 0
  to_port                 = 65535
  protocol                = "tcp"
  security_group_id       = aws_security_group.node_group.id
  source_security_group_id = aws_security_group.cluster.id
  description             = "Communication with EKS cluster"
}

# 시작 템플릿 (노드 그룹용)
resource "aws_launch_template" "node_group" {
  count = var.create_launch_template ? 1 : 0

  name_prefix = "${var.cluster_name}-eks-node-"
  instance_type = var.eks_node_instance_types[0]
  key_name      = var.ec2_key_pair_name

  vpc_security_group_ids = [aws_security_group.node_group.id]
  
  # EBS 최적화 및 암호화
  ebs_optimized = true

  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_type = var.ebs_volume_type
      volume_size = var.ebs_volume_size
      encrypted   = true
      # kms_key_id  = aws_kms_key.eks.arn
    }
  }

  # 메타데이터 서비스 설정 (보안 강화)
  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
    http_put_response_hop_limit = 1
  }

  tag_specifications {
    resource_type = "instance"
    tags = merge(var.common_tags, {
      Name = "${var.cluster_name}-eks-node"
      Type = "EKS Worker Node"
    })
  }

  tags = var.common_tags

  lifecycle {
    create_before_destroy = true
    ignore_changes = [tags_all]
  } 
}

# EKS 매니지드 노드 그룹
resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = var.node_group_name
  node_role_arn   = aws_iam_role.node_group.arn
  subnet_ids      = var.private_subnet_ids

  # 인스턴스 타입
  instance_types = var.create_launch_template ? null : var.eks_node_instance_types
  capacity_type  = var.capacity_type
  ami_type       = var.ami_type

  # 스케일링 설정
  scaling_config {
    desired_size = var.eks_node_desired_capacity
    max_size     = var.eks_node_max_capacity
    min_size     = var.eks_node_min_capacity
  }

  # 업데이트 설정
  update_config {
    max_unavailable_percentage = var.max_unavailable_percentage
  }

  # 원격 액세스 설정
  dynamic "remote_access" {
    for_each = var.enable_ssh_access ? [1] : []
    content {
      ec2_ssh_key               = var.ec2_key_pair_name
      source_security_group_ids = [aws_security_group.node_group.id]
    }
  }

  # 시작 템플릿 설정
  dynamic "launch_template" {
    for_each = var.create_launch_template ? [1] : []
    content {
      id      = aws_launch_template.node_group[0].id
      version = aws_launch_template.node_group[0].latest_version
    }
  }

  # 테인트 설정 (선택사항)
  dynamic "taint" {
    for_each = var.node_group_taints
    content {
      key    = taint.value.key
      value  = taint.value.value
      effect = taint.value.effect
    }
  }

  tags = merge(var.common_tags, {
    Name = "${var.cluster_name}-node-group"
    Type = "EKS Managed Node Group"
  })

  depends_on = [
    aws_iam_role_policy_attachment.node_group_AmazonEKSWorkerNodePolicy,
    aws_iam_role_policy_attachment.node_group_AmazonEKS_CNI_Policy,
    aws_iam_role_policy_attachment.node_group_AmazonEC2ContainerRegistryReadOnly,
    aws_iam_role_policy_attachment.node_group_CloudWatchAgentServerPolicy
  ]

  lifecycle {
    ignore_changes = [scaling_config[0].desired_size]
  }
}

# EKS 애드온들
resource "aws_eks_addon" "vpc_cni" {
  count = var.enable_vpc_cni_addon ? 1 : 0

  cluster_name             = aws_eks_cluster.main.name
  addon_name               = "vpc-cni"
  addon_version            = var.vpc_cni_addon_version
  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"
  service_account_role_arn = aws_iam_role.vpc_cni[0].arn

  tags = var.common_tags

  depends_on = [aws_eks_node_group.main]
}

resource "aws_eks_addon" "coredns" {
  count = var.enable_coredns_addon ? 1 : 0

  cluster_name      = aws_eks_cluster.main.name
  addon_name        = "coredns"
  addon_version     = var.coredns_addon_version
  resolve_conflicts = "OVERWRITE"

  tags = var.common_tags

  depends_on = [aws_eks_node_group.main]
}

resource "aws_eks_addon" "kube_proxy" {
  count = var.enable_kube_proxy_addon ? 1 : 0

  cluster_name      = aws_eks_cluster.main.name
  addon_name        = "kube-proxy"
  addon_version     = var.kube_proxy_addon_version
  resolve_conflicts = "OVERWRITE"

  tags = var.common_tags

  depends_on = [aws_eks_node_group.main]
}

# VPC CNI를 위한 IAM 역할
resource "aws_iam_role" "vpc_cni" {
  count = var.enable_vpc_cni_addon ? 1 : 0
  name  = "${var.cluster_name}-vpc-cni-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.eks[0].arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "${replace(aws_iam_openid_connect_provider.eks[0].url, "https://", "")}:sub" = "system:serviceaccount:kube-system:aws-node"
            "${replace(aws_iam_openid_connect_provider.eks[0].url, "https://", "")}:aud" = "sts.amazonaws.com"
          }
        }
      }
    ]
  })

  tags = var.common_tags
}

resource "aws_iam_role_policy_attachment" "vpc_cni" {
  count      = var.enable_vpc_cni_addon ? 1 : 0
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.vpc_cni[0].name
}

# OIDC Identity Provider
data "tls_certificate" "eks" {
  url = aws_eks_cluster.main.identity[0].oidc[0].issuer
}

resource "aws_iam_openid_connect_provider" "eks" {
  count = (var.enable_irsa || var.enable_load_balancer) ? 1 : 0

  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.eks.certificates[0].sha1_fingerprint]
  url             = aws_eks_cluster.main.identity[0].oidc[0].issuer

  tags = merge(var.common_tags, {
    Name = "${var.cluster_name}-oidc-provider"
  })
}

# =========================================
# AWS Load Balancer Controller를 위한 IAM 역할
# =========================================
data "aws_iam_policy_document" "aws_load_balancer_controller_assume_role_policy" {
  count = var.enable_load_balancer ? 1 : 0
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"

    condition {
      test     = "StringEquals"
      variable = "${replace(aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")}:sub"
      values   = ["system:serviceaccount:kube-system:aws-load-balancer-controller"]
    }

    principals {
      identifiers = [aws_iam_openid_connect_provider.eks[0].arn]
      type        = "Federated"
    }
  }
}

resource "aws_iam_role" "aws_load_balancer_controller" {
  count              = var.enable_load_balancer ? 1 : 0
  assume_role_policy = data.aws_iam_policy_document.aws_load_balancer_controller_assume_role_policy[0].json
  name               = "${var.cluster_name}-aws-load-balancer-controller"
  tags               = var.common_tags
}

resource "aws_iam_policy" "aws_load_balancer_controller" {
  count = var.enable_load_balancer && !var.use_existing_load_balancer_policy ? 1 : 0
  name  = "${var.cluster_name}-AWSLoadBalancerControllerIAMPolicy"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "iam:CreateServiceLinkedRole",
          "ec2:DescribeAccountAttributes",
          "ec2:DescribeAddresses",
          "ec2:DescribeAvailabilityZones",
          "ec2:DescribeInternetGateways",
          "ec2:DescribeVpcs",
          "ec2:DescribeSubnets",
          "ec2:DescribeSecurityGroups",
          "ec2:DescribeInstances",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DescribeTags",
          "ec2:GetCoipPoolUsage",
          "ec2:DescribeCoipPools",
          "elasticloadbalancing:DescribeLoadBalancers",
          "elasticloadbalancing:DescribeLoadBalancerAttributes",
          "elasticloadbalancing:DescribeListeners",
          "elasticloadbalancing:DescribeListenerCertificates",
          "elasticloadbalancing:DescribeSSLPolicies",
          "elasticloadbalancing:DescribeRules",
          "elasticloadbalancing:DescribeTargetGroups",
          "elasticloadbalancing:DescribeTargetGroupAttributes",
          "elasticloadbalancing:DescribeTargetHealth",
          "elasticloadbalancing:DescribeTags"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "cognito-idp:DescribeUserPoolClient",
          "acm:ListCertificates",
          "acm:DescribeCertificate",
          "iam:ListServerCertificates",
          "iam:GetServerCertificate",
          "waf-regional:GetWebACL",
          "waf-regional:GetWebACLForResource",
          "waf-regional:AssociateWebACL",
          "waf-regional:DisassociateWebACL",
          "wafv2:GetWebACL",
          "wafv2:GetWebACLForResource",
          "wafv2:AssociateWebACL",
          "wafv2:DisassociateWebACL",
          "shield:DescribeProtection",
          "shield:GetSubscriptionState",
          "shield:DescribeSubscription",
          "shield:CreateProtection",
          "shield:DeleteProtection"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateSecurityGroup",
          "ec2:CreateTags"
        ]
        Resource = "arn:aws:ec2:*:*:security-group/*"
        Condition = {
          StringEquals = {
            "ec2:CreateAction" = "CreateSecurityGroup"
          }
          Null = {
            "aws:RequestedRegion" = "false"
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "elasticloadbalancing:CreateLoadBalancer",
          "elasticloadbalancing:CreateTargetGroup"
        ]
        Resource = "*"
        Condition = {
          Null = {
            "aws:RequestedRegion" = "false"
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "elasticloadbalancing:CreateListener",
          "elasticloadbalancing:DeleteListener",
          "elasticloadbalancing:CreateRule",
          "elasticloadbalancing:DeleteRule"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "elasticloadbalancing:AddTags",
          "elasticloadbalancing:RemoveTags"
        ]
        Resource = [
          "arn:aws:elasticloadbalancing:*:*:targetgroup/*/*",
          "arn:aws:elasticloadbalancing:*:*:loadbalancer/net/*/*",
          "arn:aws:elasticloadbalancing:*:*:loadbalancer/app/*/*"
        ]
        Condition = {
          Null = {
            "aws:RequestedRegion" = "false"
            "aws:ResourceTag/elbv2.k8s.aws/cluster" = "false"
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "elasticloadbalancing:ModifyLoadBalancerAttributes",
          "elasticloadbalancing:SetIpAddressType",
          "elasticloadbalancing:SetSecurityGroups",
          "elasticloadbalancing:SetSubnets",
          "elasticloadbalancing:DeleteLoadBalancer",
          "elasticloadbalancing:ModifyTargetGroup",
          "elasticloadbalancing:ModifyTargetGroupAttributes",
          "elasticloadbalancing:DeleteTargetGroup"
        ]
        Resource = "*"
        Condition = {
          Null = {
            "aws:ResourceTag/elbv2.k8s.aws/cluster" = "false"
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "elasticloadbalancing:RegisterTargets",
          "elasticloadbalancing:DeregisterTargets"
        ]
        Resource = "arn:aws:elasticloadbalancing:*:*:targetgroup/*/*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateTags"
        ]
        Resource = "arn:aws:ec2:*:*:security-group/*"
        Condition = {
          Null = {
            "aws:ResourceTag/elbv2.k8s.aws/cluster" = "false"
            "aws:RequestedRegion" = "false"
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:AuthorizeSecurityGroupIngress",
          "ec2:RevokeSecurityGroupIngress",
          "ec2:DeleteSecurityGroup"
        ]
        Resource = "*"
        Condition = {
          Null = {
            "aws:ResourceTag/elbv2.k8s.aws/cluster" = "false"
          }
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "aws_load_balancer_controller_attach" {
  count      = var.enable_load_balancer ? 1 : 0
  role       = aws_iam_role.aws_load_balancer_controller[0].name
  policy_arn = aws_iam_policy.aws_load_balancer_controller[0].arn
}

# 현재 사용자를 관리자로 추가하기 위한 로컬 변수
locals {
  # 현재 사용자를 기본 관리자로 설정
  current_user_map = [{
    userarn  = data.aws_caller_identity.current.arn
    username = "admin"
    groups   = ["system:masters"]
  }]
  
  # 추가 관리자 사용자들
  admin_users_map = [
    for user_arn in var.cluster_admin_users : {
      userarn  = user_arn
      username = split("/", user_arn)[length(split("/", user_arn)) - 1]
      groups   = ["system:masters"]
    }
  ]
  
  # 추가 관리자 역할들
  admin_roles_map = [
    for role_arn in var.cluster_admin_roles : {
      rolearn  = role_arn
      username = split("/", role_arn)[length(split("/", role_arn)) - 1]
      groups   = ["system:masters"]
    }
  ]
  
  # 모든 사용자 매핑 결합
  all_user_mappings = concat(
    local.current_user_map,
    local.admin_users_map,
    var.map_users
  )
  
  # 모든 역할 매핑 결합 (노드 그룹 역할 + 추가 역할들)
  all_role_mappings = concat([
    {
      rolearn  = aws_iam_role.node_group.arn
      username = "system:node:{{EC2PrivateDNSName}}"
      groups   = ["system:bootstrappers", "system:nodes"]
    }
  ], local.admin_roles_map, var.map_roles)
}

