import boto3
from botocore.exceptions import ClientError
import os, sys

# 상위 디렉토리 경로 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from aws_client import AWSClientManager


import boto3
from botocore.exceptions import ClientError
import os, sys

# 상위 디렉토리 경로 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)




import boto3
from botocore.exceptions import ClientError


def check():
    """
    [1.9] MFA (Multi-Factor Authentication) 설정
    - Root 계정 및 콘솔 접속이 가능한 IAM 사용자에 대해 MFA가 활성화되어 있는지 점검
    """
    print("[INFO] 1.9 MFA 설정 체크 중...")
    iam = boto3.client('iam')
    users_without_mfa = []
    is_root_mfa_ok = False

    # 1. Root 계정 MFA 점검
    try:
        summary = iam.get_account_summary()
        if summary['SummaryMap']['AccountMFAEnabled'] == 1:
            print("[✓ COMPLIANT] 1.9 Root 계정에 MFA가 활성화되어 있습니다.")
            is_root_mfa_ok = True
        else:
            print("[⚠ WARNING] 1.9 Root 계정에 MFA가 활성화되어 있지 않습니다.")
            print("  └─ 🔧 Root 계정의 보안을 위해 즉시 MFA를 설정하세요.")
    except ClientError as e:
        print(f"[-] [ERROR] 계정 요약 정보를 가져오는 중 오류 발생: {e}")

    # 2. IAM 사용자 MFA 점검
    try:
        paginator = iam.get_paginator('list_users')
        for page in paginator.paginate():
            for user in page['Users']:
                user_name = user['UserName']
                # 콘솔 로그인이 가능한 사용자인지 확인 (패스워드 설정 여부)
                try:
                    iam.get_login_profile(UserName=user_name)
                    mfa_devices = iam.list_mfa_devices(UserName=user_name)
                    if not mfa_devices.get('MFADevices'):
                        users_without_mfa.append(user_name)
                except ClientError as e:
                    if e.response['Error']['Code'] == 'NoSuchEntity':
                        continue # 콘솔 프로필 없는 사용자
                    else:
                        raise e
        
        if not users_without_mfa:
            print("[✓ COMPLIANT] 1.9 모든 콘솔 접근 가능 IAM 사용자에게 MFA가 활성화되어 있습니다.")
        else:
            print(f"[⚠ WARNING] 1.9 MFA가 비활성화된 콘솔 접근 사용자 존재 ({len(users_without_mfa)}명)")
            print(f"  ├─ MFA 비활성 사용자: {', '.join(users_without_mfa)}")
            print("  └─ 🔧 해당 사용자들에게 MFA 설정을 강제하세요.")

    except ClientError as e:
        print(f"[-] [ERROR] IAM 사용자 MFA 정보를 가져오는 중 오류 발생: {e}")
