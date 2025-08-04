locals {
  cluster_name = var.cluster_name != "" ? var.cluster_name : "${var.project_name}-${var.environment}-eks"
}

module "vpc" {
  source = "./vpc"

  name = var.vpc_name
  cidr = var.vpc_cidr

  azs             = var.availability_zones
  public_subnets  = var.public_subnets
  private_subnets = var.private_subnets

  enable_nat_gateway     = true
  one_nat_gateway_per_az = true

  enable_dns_hostnames = true

  public_subnet_tags = {
    "kubernetes.io/cluster/${local.cluster_name}" = "shared"
    "kubernetes.io/role/elb"                      = "1"
  }

  private_subnet_tags = {
    "kubernetes.io/cluster/${local.cluster_name}" = "shared"
    "kubernetes.io/role/internal-elb"             = "1"
  }
}

# ECR 레포지토리는 이미 존재하므로 data source로 사용
data "aws_ecr_repository" "echo_app" {
  name = "walb2-app-ecr"
}

module "eks" {
  source = "./eks"

  cluster_name                    = local.cluster_name
  cluster_version                 = var.eks_cluster_version
  cluster_endpoint_private_access = false
  cluster_endpoint_public_access  = true

  cluster_addons = {
    coredns = {
      resolve_conflicts = "OVERWRITE"
    }
    kube-proxy = {}
    vpc-cni = {
      resolve_conflicts = "OVERWRITE"
    }
  }

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  cloudwatch_log_group_retention_in_days = var.cloudwatch_log_retention_days

  eks_managed_node_groups = {
    default = {
      name           = "default"
      instance_types = var.node_group_instance_types
      
      min_size     = var.node_group_min_size
      max_size     = var.node_group_max_size
      desired_size = var.node_group_desired_size

      vpc_security_group_ids = [aws_security_group.node_group_sg.id]
    }
  }
}

resource "aws_security_group" "node_group_sg" {
  name_prefix = "${local.cluster_name}-node-group-sg"
  vpc_id      = module.vpc.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${local.cluster_name}-node-group-sg"
  }
}

locals {
  lb_controller_iam_role_name        = var.lb_controller_iam_role_name
  lb_controller_service_account_name = var.lb_controller_service_account_name
}

data "aws_eks_cluster_auth" "this" {
  name = local.cluster_name
}

module "lb_controller_role" {
  source = "terraform-aws-modules/iam/aws//modules/iam-assumable-role-with-oidc"

  create_role = true

  role_name        = local.lb_controller_iam_role_name
  role_path        = "/"
  role_description = "Used by AWS Load Balancer Controller for EKS"

  role_permissions_boundary_arn = ""

  provider_url = replace(module.eks.cluster_oidc_issuer_url, "https://", "")
  oidc_fully_qualified_subjects = [
    "system:serviceaccount:kube-system:${local.lb_controller_service_account_name}"
  ]
  oidc_fully_qualified_audiences = [
    "sts.amazonaws.com"
  ]
}

data "http" "iam_policy" {
  url = "https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.4.0/docs/install/iam_policy.json"
}

resource "aws_iam_role_policy" "controller" {
  name_prefix = "AWSLoadBalancerControllerIAMPolicy"
  policy      = data.http.iam_policy.response_body
  role        = module.lb_controller_role.iam_role_name
}

resource "helm_release" "release" {
  name       = "aws-load-balancer-controller"
  chart      = "aws-load-balancer-controller"
  repository = "https://aws.github.io/eks-charts"
  namespace  = "kube-system"

  values = [
    templatefile("${path.module}/values.yaml", {
      cluster_name        = module.eks.cluster_id
      service_account_arn = module.lb_controller_role.iam_role_arn
      aws_region         = var.aws_region
      vpc_id             = module.vpc.vpc_id
      image_repository   = var.lb_controller_image_repository
      service_account_name = local.lb_controller_service_account_name
    })
  ]
}

resource "kubernetes_deployment" "echo" {
  metadata {
    name = "echo"
  }
  spec {
    replicas = 1
    selector {
      match_labels = {
        "app.kubernetes.io/name" = "echo"
      }
    }
    template {
      metadata {
        labels = {
          "app.kubernetes.io/name" = "echo"
        }
      }
      spec {
        container {
          image = "${data.aws_ecr_repository.echo_app.repository_url}:latest"
          name  = "echo"
          
          port {
            container_port = 80
            protocol       = "TCP"
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "echo" {
  metadata {
    name = "echo"
  }
  spec {
    selector = {
      "app.kubernetes.io/name" = "echo"
    }
    port {
      port        = 80
      target_port = 80
    }
    type = "NodePort"
  }
}

resource "kubernetes_ingress_v1" "alb" {
  metadata {
    name = "alb"
    annotations = {
      "alb.ingress.kubernetes.io/scheme"      = "internet-facing",
      "alb.ingress.kubernetes.io/target-type" = "ip",
    }
  }
  spec {
    ingress_class_name = "alb"
    rule {
      http {
        path {
          backend {
            service {
              name = "echo"
              port {
                number = 80
              }
            }
          }
          path = "/*"
        }
      }
    }
  }
}