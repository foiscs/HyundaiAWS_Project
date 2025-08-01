vpc_cidr           = "10.1.0.0/16"
public_subnets     = ["10.1.1.0/24", "10.1.2.0/24"]
private_subnets    = ["10.1.10.0/24", "10.1.20.0/24"] 
database_subnets   = ["10.1.100.0/24", "10.1.110.0/24"]
availability_zones = ["ap-northeast-2a", "ap-northeast-2c"]
cluster_name       = "walb2-eks-cluster"
db_name            = "musicdb"
db_user            = "msadmin"
db_password        = "MySecurePassword123!"
aws_region         = "ap-northeast-2"
environment        = "walb2"
project_name       = "walb2-app"
#create_launch_template = false
enable_load_balancer = true
# application_port 제거됨 - Ingress가 자동 관리
github_repository = "foiscs/HyundaiAWS_Project"