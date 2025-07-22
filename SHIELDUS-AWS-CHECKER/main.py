import os
import sys
import importlib
import boto3
import datetime
from contextlib import redirect_stdout

# 루트 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# 점검할 모듈 목록
CHECK_MODULES = [
    # 1. 계정 관리
    "account_management.1_1_user_account",
    "account_management.1_2_iam_user_unification",
    "account_management.1_3_iam_user_identification",
    "account_management.1_4_iam_group_membership",
    "account_management.1_5_key_pair_access",
    "account_management.1_6_key_pair_storage",
    "account_management.1_7_root_account_usage",
    "account_management.1_8_access_key_lifecycle",
    "account_management.1_9_mfa_setup",
    "account_management.1_10_password_policy",
    "account_management.1_11_eks_user_management",
    "account_management.1_12_eks_service_account",
    "account_management.1_13_eks_anonymous_access",
    # 2. 권한 관리
    "authorization.2_1_instance_service_policy",
    "authorization.2_2_network_service_policy",
    "authorization.2_3_other_service_policy",
    # 3. 가상 리소스
    "virtual_resources.3_1_sg_any_rule",
    "virtual_resources.3_2_sg_unnecessary_policy",
    "virtual_resources.3_3_nacl_traffic_policy",
    "virtual_resources.3_4_route_table_policy",
    "virtual_resources.3_5_igw_connection",
    "virtual_resources.3_6_nat_gateway_connection",
    "virtual_resources.3_7_s3_bucket_access",
    "virtual_resources.3_8_rds_subnet_az",
    "virtual_resources.3_9_eks_pod_security_policy",
    "virtual_resources.3_10_elb_connection",
    # 4. 운영 관리
    "operation.4_1_ebs_encryption",
    "operation.4_2_rds_encryption",
    "operation.4_3_s3_encryption",
    "operation.4_4_transit_encryption",
    "operation.4_5_cloudtrail_encryption",
    "operation.4_6_cloudwatch_encryption",
    "operation.4_7_user_account_logging",
    "operation.4_8_instance_logging",
    "operation.4_9_rds_logging",
    "operation.4_10_s3_bucket_logging",
    "operation.4_11_vpc_flow_logging",
    "operation.4_12_log_retention_period",
    "operation.4_13_backup_usage",
    "operation.4_14_eks_control_plane_logging",
    "operation.4_15_eks_cluster_encryption",
]

def has_aws_credentials():
    try:
        boto3.client("sts").get_caller_identity()
        return True
    except Exception:
        return False

def run_all_checks():
    print("=" * 60)
    print("      SK Shieldus AWS Security Checker Start")
    print("=" * 60)

    for module_path in CHECK_MODULES:
        try:
            module = importlib.import_module(module_path)
            if hasattr(module, "check"):
                module.check()
                print("-" * 50)
            else:
                print(f"[ERROR] '{module_path}' 모듈에 'check()' 함수가 없습니다.")
        except ImportError:
            print(f"[ERROR] '{module_path}' 모듈을 찾을 수 없습니다.")
        except Exception as e:
            print(f"[CRITICAL] '{module_path}' 점검 중 오류 발생: {e}")

if __name__ == "__main__":
    if not has_aws_credentials():
        print("[CRITICAL] 유효한 AWS 자격 증명을 찾을 수 없습니다.")
        print("[INFO] 환경변수 또는 ~/.aws/credentials 파일을 설정해 주세요.")
    else:
        # 로그 파일 생성
        log_dir = os.path.join(BASE_DIR, "logs")
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file_path = os.path.join(log_dir, f"aws_checker_log_{timestamp}.txt")

        with open(log_file_path, "w", encoding="utf-8") as log_file:
            with redirect_stdout(log_file):
                run_all_checks()
        
        # terminal에서 결과 확인
        # run_all_checks()