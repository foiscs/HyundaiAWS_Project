import boto3
from botocore.exceptions import ClientError
import os, sys

# 상위 디렉토리 경로 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from aws_client import AWSClientManager


import boto3
from botocore.exceptions import ClientError

def check():
    """
    [2.3] 기타 서비스 정책 관리 (CloudWatch, CloudTrail, KMS 등)
    - 주요 기타 서비스에 대해 과도한 권한(예: *FullAccess)이 부여되었는지 점검
    """
    print("[INFO] 2.3 기타 서비스 정책 관리 체크 중...")
    iam = boto3.client('iam')
    overly_permissive_policies = {
        "arn:aws:iam::aws:policy/CloudWatchFullAccess": "CloudWatch",
        "arn:aws:iam::aws:policy/AWSCloudTrail_FullAccess": "CloudTrail",
        "arn:aws:iam::aws:policy/AWSKeyManagementServicePowerUser": "KMS"
    }
    findings = []

    try:
        for policy_arn, service_name in overly_permissive_policies.items():
            paginator = iam.get_paginator('list_entities_for_policy')
            try:
                for page in paginator.paginate(PolicyArn=policy_arn):
                    for user in page.get('PolicyUsers', []):
                        findings.append(f"사용자 '{user['UserName']}'에 과도한 {service_name} 권한 정책('{policy_arn.split('/')[-1]}')이 연결됨")
                    for role in page.get('PolicyRoles', []):
                        findings.append(f"역할 '{role['RoleName']}'에 과도한 {service_name} 권한 정책('{policy_arn.split('/')[-1]}')이 연결됨")
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchEntity':
                    continue
                else:
                    raise e
        
        if not findings:
            print("[✓ COMPLIANT] 2.3 기타 주요 서비스에 과도한 권한(FullAccess/PowerUser)이 부여된 주체가 없습니다.")
        else:
            print(f"[⚠ WARNING] 2.3 기타 주요 서비스에 과도한 권한이 부여되었습니다 ({len(findings)}건).")
            for finding in findings:
                print(f"  ├─ {finding}")
            print("  └─ 🔧 최소 권한 원칙에 따라 필요한 작업만 허용하는 맞춤형 정책을 생성하여 적용하세요.")
    
    except ClientError as e:
        print(f"[-] [ERROR] IAM 정책 정보를 가져오는 중 오류 발생: {e}")