import boto3
from botocore.exceptions import ClientError
import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from aws_client import AWSClientManager

def check():
    """
    [1.3] IAM 사용자 계정 식별 관리
    - 모든 IAM 사용자가 식별을 위한 태그를 가지고 있는지 점검
    """
    print("[INFO] 1.3 IAM 사용자 계정 식별 관리 체크 중...")
    iam = boto3.client('iam')
    untagged_users = []

    try:
        paginator = iam.get_paginator('list_users')
        for page in paginator.paginate():
            for user in page['Users']:
                user_name = user['UserName']
                tags_response = iam.list_user_tags(UserName=user_name)
                if not tags_response.get('Tags'):
                    untagged_users.append(user_name)

        if not untagged_users:
            print("[✓ COMPLIANT] 1.3 모든 사용자 계정에 태그가 존재합니다.")
        else:
            print(f"[⚠ WARNING] 1.3 태그가 없는 사용자 계정 존재 ({len(untagged_users)}개)")
            print(f"  ├─ 태그 없는 사용자: {', '.join(untagged_users)}")
            print("  └─ 🔧 각 사용자에 식별 태그를 추가하세요 (예: 부서, 역할).")
            print("  └─ 🔧 명령어: aws iam tag-user --user-name <사용자명> --tags Key=Department,Value=<부서명> Key=Role,Value=<역할>")

    except ClientError as e:
        print(f"[-] [ERROR] IAM 사용자 태그 정보를 가져오는 중 오류 발생: {e}")