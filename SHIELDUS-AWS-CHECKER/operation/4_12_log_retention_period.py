import boto3
from botocore.exceptions import ClientError
import os, sys

# 상위 디렉토리 경로 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from aws_client import AWSClientManager


# 4.operation/4_12_log_retention_period.py
import boto3
from botocore.exceptions import ClientError

def check():
    """
    [4.12] 로그 보관 기간 설정
    - 주요 CloudWatch 로그 그룹의 보관 기간이 1년(365일) 이상으로 설정되었는지 점검
    """
    print("[INFO] 4.12 로그 보관 기간 설정 체크 중...")
    logs = boto3.client('logs')
    short_retention_groups = []

    try:
        paginator = logs.get_paginator('describe_log_groups')
        for page in paginator.paginate():
            for group in page['logGroups']:
                # CloudTrail, VPC Flow Logs, 주요 RDS 로그 등
                group_name = group['logGroupName']
                is_important_log = any(keyword in group_name for keyword in ['CloudTrail', 'vpc-flow-logs', 'RDSOSMetrics', '/aws/rds/'])

                if is_important_log:
                    if 'retentionInDays' not in group:
                        short_retention_groups.append(f"{group_name} (보관 기간: 영구)") # 영구 보관은 양호하나, 비용 측면에서 경고
                    elif group['retentionInDays'] < 365:
                         short_retention_groups.append(f"{group_name} (보관 기간: {group['retentionInDays']}일)")

        if not short_retention_groups:
            print("[✓ COMPLIANT] 4.12 주요 로그 그룹의 보관 기간이 1년 이상으로 적절히 설정되어 있습니다.")
        else:
            print(f"[⚠ WARNING] 4.12 보관 기간이 1년 미만이거나 영구 보관으로 설정된 주요 로그 그룹이 있습니다 ({len(short_retention_groups)}개).")
            for finding in short_retention_groups:
                print(f"  ├─ {finding}")
            print("  └─ 🔧 컴플라이언스 및 감사 요구사항에 맞춰 로그 보관 기간을 1년 이상으로 설정하세요.")

    except ClientError as e:
        print(f"[ERROR] CloudWatch 로그 그룹 정보를 가져오는 중 오류 발생: {e}")