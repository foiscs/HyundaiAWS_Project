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

import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)


def check():
    """
    [1.4] IAM 그룹 사용자 계정 관리
    - 모든 IAM 사용자가 하나 이상의 그룹에 속해 있는지 점검
    """
    print("[INFO] 1.4 IAM 그룹 사용자 계정 관리 체크 중...")
    iam = boto3.client('iam')
    users_not_in_group = []

    try:
        paginator = iam.get_paginator('list_users')
        for page in paginator.paginate():
            for user in page['Users']:
                user_name = user['UserName']
                groups_response = iam.list_groups_for_user(UserName=user_name)
                if not groups_response.get('Groups'):
                    users_not_in_group.append(user_name)
        
        if not users_not_in_group:
            print("[✓ COMPLIANT] 1.4 모든 사용자가 그룹에 속해 있습니다.")
        else:
            print(f"[⚠ WARNING] 1.4 그룹에 속하지 않은 사용자 존재 ({len(users_not_in_group)}개)")
            print(f"  ├─ 그룹 미소속 사용자: {', '.join(users_not_in_group)}")
            print("  └─ 🔧 권한 관리를 위해 사용자를 적절한 그룹에 추가하세요.")
            print("  └─ 🔧 명령어: aws iam add-user-to-group --user-name <사용자명> --group-name <그룹명>")
    
    except ClientError as e:
        print(f"[-] [ERROR] IAM 사용자 그룹 정보를 가져오는 중 오류 발생: {e}")