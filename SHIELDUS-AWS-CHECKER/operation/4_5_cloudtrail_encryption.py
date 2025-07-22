import boto3
from botocore.exceptions import ClientError
import os, sys

# 상위 디렉토리 경로 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from aws_client import AWSClientManager


# 4.operation/4_5_cloudtrail_encryption.py
import boto3
from botocore.exceptions import ClientError

def check():
    """
    [4.5] CloudTrail 암호화 설정
    - CloudTrail 로그 파일 암호화에 SSE-KMS가 사용되는지 점검
    """
    print("[INFO] 4.5 CloudTrail 암호화 설정 체크 중...")
    cloudtrail = boto3.client('cloudtrail')
    not_kms_encrypted_trails = []

    try:
        response = cloudtrail.describe_trails()
        for trail in response.get('trailList', []):
            if not trail.get('KmsKeyId'):
                # SSE-S3는 기본값이므로, KMS Key ID가 없는 경우 취약으로 판단
                not_kms_encrypted_trails.append(trail['Name'])
        
        if not response.get('trailList'):
             print("[INFO] 4.5 활성화된 CloudTrail이 없습니다.")
             return

        if not not_kms_encrypted_trails:
            print("[✓ COMPLIANT] 4.5 모든 CloudTrail이 SSE-KMS로 암호화되어 있습니다.")
        else:
            print(f"[⚠ WARNING] 4.5 SSE-KMS 암호화가 적용되지 않은 CloudTrail이 존재합니다 ({len(not_kms_encrypted_trails)}개).")
            print(f"  ├─ 해당 Trail: {', '.join(not_kms_encrypted_trails)}")
            print("  └─ 🔧 CloudTrail 설정에서 로그 파일 암호화를 활성화하고 관리형 키(KMS)를 지정하여 보안을 강화하세요.")
    
    except ClientError as e:
        print(f"[ERROR] CloudTrail 정보를 가져오는 중 오류 발생: {e}")