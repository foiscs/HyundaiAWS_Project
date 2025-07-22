import boto3
from botocore.exceptions import ClientError
import os, sys

# 상위 디렉토리 경로 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from aws_client import AWSClientManager


# 4.operation/4_9_rds_logging.py
import boto3
from botocore.exceptions import ClientError

def check():
    """
    [4.9] RDS 로깅 설정
    - RDS DB 인스턴스에 주요 로그(audit, error, general, slowquery 등)가 활성화되어 CloudWatch Logs로 내보내지는지 점검
    """
    print("[INFO] 4.9 RDS 로깅 설정 체크 중...")
    rds = boto3.client('rds')
    instances_with_insufficient_logging = []

    try:
        paginator = rds.get_paginator('describe_db_instances')
        for page in paginator.paginate():
            for instance in page['DBInstances']:
                enabled_logs = instance.get('EnabledCloudwatchLogsExports', [])
                # 최소한 error 로그와 audit(지원 시) 로그는 있어야 함
                if 'error' not in enabled_logs and 'audit' not in enabled_logs:
                    instances_with_insufficient_logging.append(f"{instance['DBInstanceIdentifier']} (활성 로그: {enabled_logs or '없음'})")
        
        if not instances_with_insufficient_logging:
            print("[✓ COMPLIANT] 4.9 모든 RDS DB 인스턴스에 주요 로그가 활성화되어 있습니다.")
        else:
            print(f"[⚠ WARNING] 4.9 주요 로그(Error/Audit)가 활성화되지 않은 RDS DB 인스턴스가 존재합니다 ({len(instances_with_insufficient_logging)}개).")
            for finding in instances_with_insufficient_logging:
                print(f"  ├─ {finding}")
            print("  └─ 🔧 RDS 인스턴스 수정 페이지의 [로그 내보내기] 섹션에서 Error, Audit, General, Slow-query 등 필요한 로그를 선택하여 활성화하세요.")

    except ClientError as e:
        print(f"[ERROR] RDS DB 인스턴스 정보를 가져오는 중 오류 발생: {e}")