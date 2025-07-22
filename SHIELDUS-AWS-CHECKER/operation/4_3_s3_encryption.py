import boto3
from botocore.exceptions import ClientError
import os, sys

# 상위 디렉토리 경로 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from aws_client import AWSClientManager


# 4.operation/4_3_s3_encryption.py
import boto3
from botocore.exceptions import ClientError

def check():
    """
    [4.3] S3 암호화 설정
    - S3 버킷에 기본 암호화가 설정되어 있는지 점검
    """
    print("[INFO] 4.3 S3 암호화 설정 체크 중...")
    s3 = boto3.client('s3')
    unencrypted_buckets = []

    try:
        response = s3.list_buckets()
        for bucket in response['Buckets']:
            bucket_name = bucket['Name']
            try:
                # 기본 암호화 설정이 없으면 GetBucketEncryption은 예외를 발생시킴
                s3.get_bucket_encryption(Bucket=bucket_name)
            except ClientError as e:
                if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                    unencrypted_buckets.append(bucket_name)
                else:
                    print(f"[ERROR] 버킷 '{bucket_name}'의 암호화 정보 확인 중 오류: {e}")
        
        if not unencrypted_buckets:
            print("[✓ COMPLIANT] 4.3 모든 S3 버킷에 기본 암호화가 설정되어 있습니다.")
        else:
            print(f"[⚠ WARNING] 4.3 기본 암호화가 설정되지 않은 S3 버킷이 존재합니다 ({len(unencrypted_buckets)}개).")
            print(f"  ├─ 해당 버킷: {', '.join(unencrypted_buckets)}")
            print("  └─ 🔧 S3 버킷의 [속성] 탭에서 [기본 암호화]를 활성화하세요 (SSE-S3 또는 SSE-KMS).")

    except ClientError as e:
        print(f"[ERROR] S3 버킷 목록을 가져오는 중 오류 발생: {e}")