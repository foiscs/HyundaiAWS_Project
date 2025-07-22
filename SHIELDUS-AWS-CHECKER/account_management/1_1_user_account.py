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

import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)




def check():
    """
    [1.1] 사용자 계정 관리
    - AdministratorAccess 권한을 가진 IAM 사용자가 최소한으로 유지되는지 점검
    - 기준: 관리자 권한을 가진 사용자가 3명 이상일 경우 WARNING
    """
    print("[INFO] 1.1 사용자 계정 관리 체크 중...")
    iam = boto3.client('iam')
    policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
    admin_users = []
    
    try:
        # 정책에 연결된 모든 사용자 목록 가져오기
        response = iam.list_entities_for_policy(PolicyArn=policy_arn)
        admin_users.extend([user['UserName'] for user in response.get('PolicyUsers', [])])

        # 페이징 처리
        while response.get('IsTruncated'):
            response = iam.list_entities_for_policy(PolicyArn=policy_arn, Marker=response['Marker'])
            admin_users.extend([user['UserName'] for user in response.get('PolicyUsers', [])])

        if not admin_users:
            print("[✓ COMPLIANT] 1.1 관리자 권한(AdministratorAccess)을 가진 사용자가 없습니다.")
        elif len(admin_users) < 3:
            print(f"[✓ COMPLIANT] 1.1 관리자 권한 사용자 수가 적절함 ({len(admin_users)}명)")
            print(f"  └─ 관리자: {', '.join(admin_users)}")
        else:
            print(f"[⚠ WARNING] 1.1 관리자 권한(AdministratorAccess)을 가진 사용자가 많습니다. ({len(admin_users)}명)")
            print(f"  ├─ 관리자 목록: {', '.join(admin_users)}")
            print("  └─ 🔧 불필요한 관리자 계정의 권한을 축소하세요.")
            print("  └─ 🔧 명령어: aws iam detach-user-policy --user-name <사용자명> --policy-arn arn:aws:iam::aws:policy/AdministratorAccess")

    except ClientError as e:
        print(f"[ERROR] 사용자 계정 정보를 가져오는 중 오류 발생: {e}")