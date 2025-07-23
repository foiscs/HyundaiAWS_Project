# main.py
import os
import sys
import importlib
import boto3
import datetime
import traceback
from collections import OrderedDict

# --- 프로젝트 경로 설정 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# --- 점검할 모듈 목록 (OrderedDict로 순서 보장) ---
CHECK_MODULES = OrderedDict([
    # 1. 계정 관리
    ("account_management.1_1_user_account", "1.1 사용자 계정 관리"),
    ("account_management.1_2_iam_user_unification", "1.2 IAM 사용자 계정 단일화 관리"),
    ("account_management.1_3_iam_user_identification", "1.3 IAM 사용자 계정 식별 관리"),
    ("account_management.1_4_iam_group_membership", "1.4 IAM 그룹 사용자 계정 관리"),
    ("account_management.1_5_key_pair_access", "1.5 Key Pair 접근 관리"),
    ("account_management.1_6_key_pair_storage", "1.6 Key Pair 보관 관리"),
    ("account_management.1_7_root_account_usage", "1.7 Root 계정 사용 관리"),
    ("account_management.1_8_access_key_lifecycle", "1.8 Access Key 수명 주기 관리"),
    ("account_management.1_9_mfa_setup", "1.9 MFA 설정"),
    ("account_management.1_10_password_policy", "1.10 패스워드 정책 관리"),
    ("account_management.1_11_eks_user_management", "1.11 EKS 사용자 관리"),
    ("account_management.1_12_eks_service_account", "1.12 EKS 서비스 어카운트 관리"),
    ("account_management.1_13_eks_anonymous_access", "1.13 EKS 익명 접근 관리"),
    # 2. 권한 관리
    ("authorization.2_1_instance_service_policy", "2.1 인스턴스 서비스 정책 관리"),
    ("authorization.2_2_network_service_policy", "2.2 네트워크 서비스 정책 관리"),
    ("authorization.2_3_other_service_policy", "2.3 기타 서비스 정책 관리"),
    # 3. 가상 리소스
    ("virtual_resources.3_1_sg_any_rule", "3.1 보안 그룹 ANY 규칙 관리"),
    ("virtual_resources.3_2_sg_unnecessary_policy", "3.2 보안 그룹 불필요 정책 관리"),
    ("virtual_resources.3_3_nacl_traffic_policy", "3.3 NACL 트래픽 정책 관리"),
    ("virtual_resources.3_4_route_table_policy", "3.4 라우팅 테이블 정책 관리"),
    ("virtual_resources.3_5_igw_connection", "3.5 인터넷 게이트웨이 연결 관리"),
    ("virtual_resources.3_6_nat_gateway_connection", "3.6 NAT 게이트웨이 연결 관리"),
    ("virtual_resources.3_7_s3_bucket_access", "3.7 S3 버킷 접근 관리"),
    ("virtual_resources.3_8_rds_subnet_az", "3.8 RDS 서브넷 가용 영역 관리"),
    ("virtual_resources.3_9_eks_pod_security_policy", "3.9 EKS Pod 보안 정책 관리"),
    ("virtual_resources.3_10_elb_connection", "3.10 ELB 연결 관리"),
    # 4. 운영 관리
    ("operation.4_1_ebs_encryption", "4.1 EBS 암호화 설정"),
    ("operation.4_2_rds_encryption", "4.2 RDS 암호화 설정"),
    ("operation.4_3_s3_encryption", "4.3 S3 암호화 설정"),
    ("operation.4_4_transit_encryption", "4.4 통신 구간 암호화 설정"),
    ("operation.4_5_cloudtrail_encryption", "4.5 CloudTrail 암호화 설정"),
    ("operation.4_6_cloudwatch_encryption", "4.6 CloudWatch 암호화 설정"),
    ("operation.4_7_user_account_logging", "4.7 사용자 계정 로깅 설정"),
    ("operation.4_8_instance_logging", "4.8 인스턴스 로깅 설정"),
    ("operation.4_9_rds_logging", "4.9 RDS 로깅 설정"),
    ("operation.4_10_s3_bucket_logging", "4.10 S3 버킷 로깅 설정"),
    ("operation.4_11_vpc_flow_logging", "4.11 VPC 플로우 로깅 설정"),
    ("operation.4_12_log_retention_period", "4.12 로그 보관 기간 설정"),
    ("operation.4_13_backup_usage", "4.13 백업 사용 여부"),
    ("operation.4_14_eks_control_plane_logging", "4.14 EKS 제어 플레인 로깅 설정"),
    ("operation.4_15_eks_cluster_encryption", "4.15 EKS 클러스터 암호화 설정"),
])

# --- Helper Classes & Functions ---

class Tee(object):
    """터미널과 파일에 동시에 출력하기 위한 클래스"""
    def __init__(self, *files):
        self.files = files
    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()
    def flush(self):
        for f in self.files:
            f.flush()

def has_aws_credentials():
    """AWS 자격 증명 유효성 확인"""
    try:
        boto3.client("sts").get_caller_identity()
        return True
    except Exception:
        return False

# --- Core Logic ---

def run_all_checks():
    """모든 점검을 실행하고 취약점 결과를 수집"""
    print("=" * 70)
    print("      SK Shieldus AWS Security Checker - 점검을 시작합니다.")
    print("=" * 70)

    vulnerabilities = OrderedDict()
    for module_path, description in CHECK_MODULES.items():
        try:
            module = importlib.import_module(module_path)
            if hasattr(module, "check"):
                # check() 함수의 반환값을 받아 취약점 여부 판단
                findings = module.check()
                # 반환값이 'truthy'(내용이 있는 list, dict, True 등)이면 취약점으로 간주
                if findings:
                    vulnerabilities[module_path] = findings
                print("-" * 70)
            else:
                print(f"[ERROR] '{module_path}' 모듈에 'check()' 함수가 없습니다.")
        except ImportError:
            print(f"[ERROR] '{module_path}' 모듈을 찾을 수 없습니다.")
        except Exception:
            print(f"[CRITICAL] '{description}' 점검 중 오류 발생:")
            traceback.print_exc()
            print("-" * 70)
    return vulnerabilities

def display_summary_and_get_consent(vulnerabilities):
    """점검 결과를 요약하고 사용자에게 조치 여부를 물음"""
    print("=" * 70)
    print("      점검 완료: 취약점 요약")
    print("=" * 70)
    
    if not vulnerabilities:
        print("\n[🎉 축하합니다! 발견된 취약점이 없습니다.]\n")
        return False

    for module_path in vulnerabilities:
        description = CHECK_MODULES.get(module_path, module_path)
        print(f"[!] 취약점 발견: {description}")

    print("-" * 70)
    try:
        choice = input("\n[?] 위에 요약된 취약점 항목에 대한 일괄 조치를 진행하시겠습니까? (y/n): ").lower()
        return choice == 'y'
    except KeyboardInterrupt:
        print("\n사용자 요청으로 종료합니다.")
        return False

def run_all_fixes(vulnerabilities):
    """발견된 취약점에 대한 조치를 순차적으로 실행"""
    print("\n" + "=" * 70)
    print("      취약점 자동/수동 조치를 시작합니다.")
    print("=" * 70)

    for module_path, findings in vulnerabilities.items():
        description = CHECK_MODULES.get(module_path, module_path)
        print(f"-> 조치 진행 중: {description}")
        try:
            module = importlib.import_module(module_path)
            if hasattr(module, "fix"):
                module.fix(findings)
            else:
                print(f"   [INFO] '{description}' 항목에 대한 자동 조치(fix)가 정의되지 않았습니다.")
            print("-" * 70)
        except Exception:
            print(f"[CRITICAL] '{description}' 조치 중 오류 발생:")
            traceback.print_exc()
            print("-" * 70)

# --- Main Execution ---

if __name__ == "__main__":
    if not has_aws_credentials():
        print("[CRITICAL] 유효한 AWS 자격 증명을 찾을 수 없습니다.")
        print("[INFO] 환경변수 또는 `aws configure`를 통해 자격 증명을 설정해 주세요.")
    else:
        # 로그 파일 설정
        log_dir = os.path.join(BASE_DIR, "logs")
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file_path = os.path.join(log_dir, f"aws_security_check_{timestamp}.log")

        original_stdout = sys.stdout
        with open(log_file_path, "w", encoding="utf-8") as log_file:
            # 터미널과 파일에 동시 출력
            sys.stdout = Tee(original_stdout, log_file)
            
            # 1. 점검 실행 및 결과 수집
            found_vulnerabilities = run_all_checks()
            
            # 원본 stdout으로 복원하여 사용자 입력 받기
            sys.stdout = original_stdout
            
            # 2. 요약 및 조치 동의
            if display_summary_and_get_consent(found_vulnerabilities):
                # 3. 조치 실행 (다시 Tee로 출력)
                sys.stdout = Tee(original_stdout, log_file)
                run_all_fixes(found_vulnerabilities)
                print("\n[+] 모든 조치 과정이 완료되었습니다.")
            else:
                print("\n[-] 조치를 실행하지 않고 프로그램을 종료합니다.")
            
            # 최종적으로 stdout 복원
            sys.stdout = original_stdout
            print(f"\n[+] 모든 결과가 다음 파일에 저장되었습니다: {log_file_path}")