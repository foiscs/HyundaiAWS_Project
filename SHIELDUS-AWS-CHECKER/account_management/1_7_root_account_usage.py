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
    [1.7] Admin Console(Root) 관리자 정책 관리
    - Root 계정에 Access Key가 생성되어 있는지 점검. Root 계정의 Access Key는 사용하지 않는 것이 강력히 권장됨
    """
    print("[INFO] 1.7 Admin Console(Root) 관리자 정책 관리 체크 중...")
    iam = boto3.client('iam')

    try:
        summary = iam.get_account_summary()
        if summary['SummaryMap']['AccountAccessKeysPresent'] == 1:
            print("[⚠ WARNING] 1.7 Root 계정에 Access Key가 존재합니다.")
            print("  ├─ Root 계정의 Access Key는 일상적인 작업에 사용해서는 안 됩니다.")
            print("  └─ 🔧 Access Key가 불필요한 경우 즉시 삭제하고, 필요 시 IAM 사용자를 생성하여 사용하세요.")
            print("  └─ 🔧 가이드: AWS Management Console에 Root 계정으로 로그인하여 [내 보안 자격 증명]에서 Access Key를 삭제합니다.")
        else:
            print("[✓ COMPLIANT] 1.7 Root 계정에 Access Key가 생성되어 있지 않습니다.")

    except ClientError as e:
        print(f"[-] [ERROR] 계정 요약 정보를 가져오는 중 오류 발생: {e}")