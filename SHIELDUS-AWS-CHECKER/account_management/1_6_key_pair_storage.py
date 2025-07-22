import boto3
from botocore.exceptions import ClientError
import os, sys

# 상위 디렉토리 경로 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from aws_client import AWSClientManager

def check():
    """
    [1.6] Key Pair 보관 관리
    - 공개적으로 접근 가능한 S3 버킷에 Key Pair(.pem) 파일이 저장되어 있는지 점검
    """
    print("[INFO] 1.6 Key Pair 보관 관리 체크 중...")
    s3 = boto3.client('s3')
    found_vulnerable_keys = False

    try:
        response = s3.list_buckets()
        for bucket in response['Buckets']:
            bucket_name = bucket['Name']
            is_public = False
            
            # 1. Public Access Block 설정 확인
            try:
                pab_response = s3.get_public_access_block(Bucket=bucket_name)
                pab_config = pab_response['PublicAccessBlockConfiguration']
                if not (pab_config.get('BlockPublicAcls', False) and
                        pab_config.get('IgnorePublicAcls', False) and
                        pab_config.get('BlockPublicPolicy', False) and
                        pab_config.get('RestrictPublicBuckets', False)):
                    is_public = True # 하나라도 False이면 공개 가능성이 있음
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchPublicAccessBlockConfiguration':
                    is_public = True # 설정이 없으면 기본적으로 공개 가능
                else:
                    print(f"[-] [ERROR] {bucket_name}의 Public Access Block 확인 중 오류: {e}")
                    continue

            # 2. 버킷 정책(Policy) 확인
            if not is_public:
                try:
                    policy_status = s3.get_bucket_policy_status(Bucket=bucket_name)
                    if policy_status['PolicyStatus']['IsPublic']:
                        is_public = True
                except ClientError as e:
                    if e.response['Error']['Code'] != 'NoSuchBucketPolicy':
                         is_public = True

            if is_public:
                try:
                    paginator = s3.get_paginator('list_objects_v2')
                    for page in paginator.paginate(Bucket=bucket_name):
                        for obj in page.get('Contents', []):
                            if obj['Key'].lower().endswith('.pem'):
                                if not found_vulnerable_keys:
                                    print(f"[⚠ WARNING] 1.6 공개 가능한 S3 버킷에 Key Pair 파일(.pem)이 존재합니다.")
                                    found_vulnerable_keys = True
                                print(f"  ├─ 버킷: {bucket_name}, 키: {obj['Key']}")
                except ClientError as e:
                    # 일부 버킷은 권한 부족으로 리스팅이 안될 수 있음
                    if e.response['Error']['Code'] == 'AccessDenied':
                        print(f"[-] [INFO] 버킷 '{bucket_name}'의 객체 목록을 확인할 권한이 없습니다.")
                    else:
                        print(f"[-] [ERROR] {bucket_name}의 객체 목록 확인 중 오류: {e}")

        if not found_vulnerable_keys:
            print("[✓ COMPLIANT] 1.6 공개 가능한 S3 버킷에서 Key Pair 파일이 발견되지 않았습니다.")
        else:
             print("  └─ 🔧 해당 Key Pair 파일을 즉시 삭제하거나 비공개 버킷으로 이동하고, 버킷의 공개 설정을 비활성화하세요.")

    except ClientError as e:
        print(f"[-] [ERROR] S3 버킷 정보를 가져오는 중 오류 발생: {e}")