import boto3
from botocore.exceptions import ClientError
import os, sys

# 상위 디렉토리 경로 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from aws_client import AWSClientManager


# 4.operation/4_10_s3_bucket_logging.py
import boto3
from botocore.exceptions import ClientError

def check():
    """
    [4.10] S3 버킷 로깅 설정
    - S3 버킷에 서버 액세스 로깅이 활성화되어 있는지 점검
    """
    print("[INFO] 4.10 S3 버킷 로깅 설정 체크 중...")
    s3 = boto3.client('s3')
    logging_disabled_buckets = []

    try:
        response = s3.list_buckets()
        for bucket in response['Buckets']:
            bucket_name = bucket['Name']
            try:
                logging_info = s3.get_bucket_logging(Bucket=bucket_name)
                # LoggingEnabled 키가 없으면 로깅이 비활성화된 것
                if 'LoggingEnabled' not in logging_info:
                    logging_disabled_buckets.append(bucket_name)
            except ClientError as e:
                print(f"[ERROR] 버킷 '{bucket_name}'의 로깅 정보 확인 중 오류: {e}")
        
        if not logging_disabled_buckets:
            print("[✓ COMPLIANT] 4.10 모든 S3 버킷에 서버 액세스 로깅이 활성화되어 있습니다.")
        else:
            print(f"[⚠ WARNING] 4.10 서버 액세스 로깅이 비활성화된 S3 버킷이 존재합니다 ({len(logging_disabled_buckets)}개).")
            # 로그 대상 버킷 자체는 로깅할 수 없으므로 점검 결과에서 제외할 수 있음
            print(f"  ├─ 해당 버킷: {', '.join(b for b in logging_disabled_buckets if 'log' not in b.lower())}")
            print("  └─ 🔧 S3 버킷의 [속성] 탭에서 [서버 액세스 로깅]을 활성화하여 객체 수준의 요청을 기록하세요.")

    except ClientError as e:
        print(f"[ERROR] S3 버킷 목록을 가져오는 중 오류 발생: {e}")