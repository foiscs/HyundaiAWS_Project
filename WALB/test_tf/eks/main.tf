# EKS Module
# terraform-aws-modules/eks/aws와 호환되는 EKS 모듈

data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}

# EKS 클러스터 서비스 역할
resource "aws_iam_role" "cluster" {
  name = "${var.cluster_name}-cluster-role"

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

  tags = var.tags
}

# EKS 클러스터 서비스 역할 정책 연결
resource "aws_iam_role_policy_attachment" "cluster_AmazonEKSClusterPolicy" {
  policy_arn = "arn:${data.aws_partition.current.partition}:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.cluster.name
}

# CloudWatch 로그 그룹
resource "aws_cloudwatch_log_group" "this" {
  count = var.create_cloudwatch_log_group ? 1 : 0

  name              = "/aws/eks/${var.cluster_name}/cluster"
  retention_in_days = var.cloudwatch_log_group_retention_in_days

  tags = var.tags
}

# EKS 클러스터
resource "aws_eks_cluster" "this" {
  name     = var.cluster_name
  role_arn = aws_iam_role.cluster.arn
  version  = var.cluster_version

  vpc_config {
    subnet_ids              = var.subnet_ids
    endpoint_private_access = var.cluster_endpoint_private_access
    endpoint_public_access  = var.cluster_endpoint_public_access
    public_access_cidrs     = var.cluster_endpoint_public_access_cidrs
  }

  enabled_cluster_log_types = var.cluster_enabled_log_types

  depends_on = [
    aws_iam_role_policy_attachment.cluster_AmazonEKSClusterPolicy,
    aws_cloudwatch_log_group.this
  ]

  tags = var.tags
}

# EKS 애드온들
resource "aws_eks_addon" "this" {
  for_each = var.cluster_addons

  cluster_name             = aws_eks_cluster.this.name
  addon_name               = each.key
  addon_version            = lookup(each.value, "addon_version", null)
  resolve_conflicts_on_create = lookup(each.value, "resolve_conflicts", "OVERWRITE")
  resolve_conflicts_on_update = lookup(each.value, "resolve_conflicts", "OVERWRITE")
  service_account_role_arn = lookup(each.value, "service_account_role_arn", null)

  tags = var.tags

  depends_on = [aws_eks_node_group.this]
}

# 노드 그룹 IAM 역할
resource "aws_iam_role" "node_group" {
  for_each = var.eks_managed_node_groups

  name = "${var.cluster_name}-${each.key}-node-group-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# 노드 그룹 IAM 정책들
resource "aws_iam_role_policy_attachment" "node_group_AmazonEKSWorkerNodePolicy" {
  for_each = var.eks_managed_node_groups

  policy_arn = "arn:${data.aws_partition.current.partition}:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.node_group[each.key].name
}

resource "aws_iam_role_policy_attachment" "node_group_AmazonEKS_CNI_Policy" {
  for_each = var.eks_managed_node_groups

  policy_arn = "arn:${data.aws_partition.current.partition}:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.node_group[each.key].name
}

resource "aws_iam_role_policy_attachment" "node_group_AmazonEC2ContainerRegistryReadOnly" {
  for_each = var.eks_managed_node_groups

  policy_arn = "arn:${data.aws_partition.current.partition}:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.node_group[each.key].name
}

# EKS 노드 그룹
resource "aws_eks_node_group" "this" {
  for_each = var.eks_managed_node_groups

  cluster_name    = aws_eks_cluster.this.name
  node_group_name = lookup(each.value, "name", each.key)
  node_role_arn   = aws_iam_role.node_group[each.key].arn
  subnet_ids      = var.subnet_ids

  instance_types = lookup(each.value, "instance_types", ["t3.medium"])
  capacity_type  = lookup(each.value, "capacity_type", "ON_DEMAND")
  ami_type       = lookup(each.value, "ami_type", "AL2_x86_64")

  scaling_config {
    desired_size = lookup(each.value, "desired_size", 1)
    max_size     = lookup(each.value, "max_size", 3)
    min_size     = lookup(each.value, "min_size", 1)
  }

  update_config {
    max_unavailable_percentage = lookup(each.value, "max_unavailable_percentage", 25)
  }

  # 추가 보안 그룹 ID들
  dynamic "remote_access" {
    for_each = lookup(each.value, "key_name", null) != null ? [1] : []
    content {
      ec2_ssh_key               = lookup(each.value, "key_name", null)
      source_security_group_ids = lookup(each.value, "vpc_security_group_ids", [])
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.node_group_AmazonEKSWorkerNodePolicy,
    aws_iam_role_policy_attachment.node_group_AmazonEKS_CNI_Policy,
    aws_iam_role_policy_attachment.node_group_AmazonEC2ContainerRegistryReadOnly,
  ]

  tags = merge(var.tags, lookup(each.value, "tags", {}))
}

# OIDC Identity Provider
data "tls_certificate" "this" {
  url = aws_eks_cluster.this.identity[0].oidc[0].issuer
}

resource "aws_iam_openid_connect_provider" "this" {
  count = var.enable_irsa ? 1 : 0

  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.this.certificates[0].sha1_fingerprint]
  url             = aws_eks_cluster.this.identity[0].oidc[0].issuer

  tags = var.tags
}