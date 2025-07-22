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


def check():
    """
    [1.8] Admin Console 계정 Access Key 활성화 및 사용주기 관리
    - 생성된 지 60일이 지난 IAM 사용자의 Access Key를 점검
    - 30일 이상 사용되지 않은 Access Key를 점검
    """
    print("[INFO] 1.8 Access Key 활성화 및 사용주기 관리 체크 중...")
    iam = boto3.client('iam')
    old_keys = []
    unused_keys = []
    now = datetime.now(timezone.utc)

    try:
        paginator = iam.get_paginator('list_users')
        for page in paginator.paginate():
            for user in page['Users']:
                user_name = user['UserName']
                keys_response = iam.list_access_keys(UserName=user_name)
                for key in keys_response['AccessKeyMetadata']:
                    if key['Status'] == 'Active':
                        access_key_id = key['AccessKeyId']
                        create_date = key['CreateDate']
                        
                        # 생성일 기준 60일 초과 점검
                        if (now - create_date).days > 60:
                            old_keys.append(f"{user_name}의 키 ({access_key_id}, 생성 후 {(now - create_date).days}일)")

                        # 마지막 사용일 기준 30일 초과 점검
                        last_used_info = iam.get_access_key_last_used(AccessKeyId=access_key_id)
                        last_used_date = last_used_info.get('AccessKeyLastUsed', {}).get('LastUsedDate')
                        if last_used_date:
                            if (now - last_used_date).days > 30:
                                unused_keys.append(f"{user_name}의 키 ({access_key_id}, 미사용 {(now - last_used_date).days}일)")
                        # 사용 기록이 없으면 생성일 기준 30일 초과 시 미사용으로 간주
                        elif (now - create_date).days > 30:
                            unused_keys.append(f"{user_name}의 키 ({access_key_id}, 사용기록 없음, 생성 후 {(now - create_date).days}일)")

        if not old_keys and not unused_keys:
            print("[✓ COMPLIANT] 1.8 모든 활성 Access Key가 주기 관리 기준을 준수합니다.")
        
        if old_keys:
            print(f"[⚠ WARNING] 1.8 생성된 지 60일이 경과한 Access Key가 존재합니다 ({len(old_keys)}개).")
            for key_info in old_keys:
                print(f"  ├─ {key_info}")
            print("  └─ 🔧 주기적인 Access Key 교체(Rotation)를 권장합니다.")
        
        if unused_keys:
            print(f"[⚠ WARNING] 1.8 30일 이상 사용되지 않은 Access Key가 존재합니다 ({len(unused_keys)}개).")
            for key_info in unused_keys:
                print(f"  ├─ {key_info}")
            print("  └─ 🔧 사용하지 않는 Access Key는 비활성화하거나 삭제하세요.")
            print("  └─ 🔧 명령어 (비활성화): aws iam update-access-key --access-key-id <ACCESS_KEY_ID> --status Inactive --user-name <사용자명>")


    except ClientError as e:
        print(f"[-] [ERROR] Access Key 정보를 가져오는 중 오류 발생: {e}")