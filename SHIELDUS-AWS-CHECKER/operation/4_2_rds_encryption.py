import boto3
from botocore.exceptions import ClientError
import os, sys

# 상위 디렉토리 경로 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from aws_client import AWSClientManager


# 4.operation/4_2_rds_encryption.py
import boto3
from botocore.exceptions import ClientError

def check():
    """
    [4.2] RDS 암호화 설정
    - 암호화되지 않은 RDS DB 인스턴스가 있는지 점검
    """
    print("[INFO] 4.2 RDS 암호화 설정 체크 중...")
    rds = boto3.client('rds')
    unencrypted_instances = []

    try:
        paginator = rds.get_paginator('describe_db_instances')
        for page in paginator.paginate():
            for instance in page['DBInstances']:
                if not instance.get('StorageEncrypted'):
                    unencrypted_instances.append(instance['DBInstanceIdentifier'])

        if not unencrypted_instances:
            print("[✓ COMPLIANT] 4.2 모든 RDS DB 인스턴스가 암호화되어 있습니다.")
        else:
            print(f"[⚠ WARNING] 4.2 스토리지 암호화가 비활성화된 RDS DB 인스턴스가 존재합니다 ({len(unencrypted_instances)}개).")
            print(f"  ├─ 해당 인스턴스: {', '.join(unencrypted_instances)}")
            print("  └─ 🔧 암호화는 인스턴스 생성 시에만 가능합니다. 암호화된 스냅샷을 생성한 후, 해당 스냅샷으로 새 인스턴스를 복원하여 마이그레이션하세요.")
    
    except ClientError as e:
        print(f"[ERROR] RDS DB 인스턴스 정보를 가져오는 중 오류 발생: {e}")