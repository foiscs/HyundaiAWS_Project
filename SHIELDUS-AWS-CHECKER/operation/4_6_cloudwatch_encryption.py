import boto3
from botocore.exceptions import ClientError
import os, sys

# 상위 디렉토리 경로 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from aws_client import AWSClientManager


# 4.operation/4_6_cloudwatch_encryption.py
import boto3
from botocore.exceptions import ClientError

def check():
    """
    [4.6] CloudWatch 암호화 설정
    - CloudWatch Logs 로그 그룹이 KMS로 암호화되었는지 점검
    """
    print("[INFO] 4.6 CloudWatch 암호화 설정 체크 중...")
    logs = boto3.client('logs')
    unencrypted_log_groups = []

    try:
        paginator = logs.get_paginator('describe_log_groups')
        for page in paginator.paginate():
            for group in page['logGroups']:
                if 'kmsKeyId' not in group:
                    unencrypted_log_groups.append(group['logGroupName'])

        if not unencrypted_log_groups:
            print("[✓ COMPLIANT] 4.6 모든 CloudWatch 로그 그룹이 KMS로 암호화되어 있습니다.")
        else:
            print(f"[⚠ WARNING] 4.6 KMS 암호화가 적용되지 않은 CloudWatch 로그 그룹이 존재합니다 ({len(unencrypted_log_groups)}개).")
            # 결과가 너무 많을 수 있으므로 일부만 표시
            display_count = 5
            for group_name in unencrypted_log_groups[:display_count]:
                print(f"  ├─ {group_name}")
            if len(unencrypted_log_groups) > display_count:
                print(f"  └─ ... 외 {len(unencrypted_log_groups) - display_count}개 더 있음")
            print("  └─ 🔧 로그 그룹 생성 시 또는 기존 로그 그룹에 대해 KMS 키를 연결하여 암호화를 활성화하세요.")
            print("  └─ 🔧 명령어: aws logs associate-kms-key --log-group-name <그룹명> --kms-key-id <KMS_KEY_ARN>")

    except ClientError as e:
        print(f"[ERROR] CloudWatch 로그 그룹 정보를 가져오는 중 오류 발생: {e}")