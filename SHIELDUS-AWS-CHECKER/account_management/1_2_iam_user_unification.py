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
from datetime import datetime, timezone
import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)


def check():
    """
    [1.2] IAM 사용자 계정 단일화 관리
    - 90일 이상 사용되지 않은 IAM 사용자를 비활성 계정으로 간주하여 점검
    - 이는 '1인 1계정' 원칙 위반이나 불필요한 테스트/퇴사자 계정 존재 가능성을 시사
    """
    print("[INFO] 1.2 IAM 사용자 계정 단일화 관리 체크 중...")
    iam = boto3.client('iam')
    inactive_users = []
    now = datetime.now(timezone.utc)

    try:
        paginator = iam.get_paginator('list_users')
        for page in paginator.paginate():
            for user in page['Users']:
                user_name = user['UserName']
                
                # 사용자의 마지막 활동 정보 확인
                if 'PasswordLastUsed' in user:
                    last_activity = user['PasswordLastUsed']
                    if (now - last_activity).days > 90:
                        inactive_users.append(f"{user_name} (콘솔 비활성: {(now - last_activity).days}일)")
                        continue # 다음 사용자로

                # Access Key 마지막 사용 정보 확인
                keys_response = iam.list_access_keys(UserName=user_name)
                if not keys_response['AccessKeyMetadata']: # 키가 없는 사용자
                    if 'PasswordLastUsed' not in user: # 콘솔 사용 기록도 없으면
                        inactive_users.append(f"{user_name} (활동 기록 없음)")
                    continue

                is_active_key_found = False
                for key in keys_response['AccessKeyMetadata']:
                    if key['Status'] == 'Active':
                        last_used_info = iam.get_access_key_last_used(AccessKeyId=key['AccessKeyId'])
                        if 'LastUsedDate' in last_used_info['AccessKeyLastUsed']:
                            last_used_date = last_used_info['AccessKeyLastUsed']['LastUsedDate']
                            if (now - last_used_date).days <= 90:
                                is_active_key_found = True
                                break # 활성 키를 찾았으므로 이 사용자는 활성 상태
                        # LastUsedDate가 없는 경우, 생성일 기준 90일 경과 시 비활성으로 간주
                        elif (now - key['CreateDate']).days > 90:
                           pass # 비활성 후보로 남음
                        else:
                           is_active_key_found = True
                           break
                
                if not is_active_key_found:
                    inactive_users.append(f"{user_name} (액세스 키 비활성: 90+일)")

        if not inactive_users:
            print("[✓ COMPLIANT] 1.2 장기 미사용 또는 불필요한 사용자 계정이 발견되지 않았습니다.")
        else:
            print(f"[⚠ WARNING] 1.2 장기 미사용(90일 이상) 사용자 계정이 존재합니다 ({len(inactive_users)}개).")
            for user_info in inactive_users:
                print(f"  ├─ 비활성 의심 사용자: {user_info}")
            print("  └─ 🔧 퇴사자, 테스트, 불필요한 계정은 삭제하거나 비활성화하세요.")
            print("  └─ 🔧 명령어 (비활성화): aws iam deactivate-login-profile --user-name <사용자명>")
            print("  └─ 🔧 명령어 (삭제): aws iam delete-user --user-name <사용자명>")

    except ClientError as e:
        print(f"[-] [ERROR] IAM 사용자 활동 정보를 가져오는 중 오류 발생: {e}")
