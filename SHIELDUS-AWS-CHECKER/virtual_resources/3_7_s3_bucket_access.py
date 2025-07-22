import boto3
from botocore.exceptions import ClientError
import os, sys

# 상위 디렉토리 경로 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from aws_client import AWSClientManager
import json

def check():
    """
    [3.7] S3 버킷/객체 접근 관리
    - 퍼블릭 액세스 차단이 비활성화되었거나, ACL 또는 정책에 의해 공개된 S3 버킷을 점검
    """
    print("[INFO] 3.7 S3 버킷/객체 접근 관리 체크 중...")
    s3 = boto3.client('s3')
    public_buckets_reasons = {}

    try:
        response = s3.list_buckets()
        for bucket in response['Buckets']:
            bucket_name = bucket['Name']
            reasons = []
            
            # 1. Public Access Block 설정 확인
            try:
                pab = s3.get_public_access_block(Bucket=bucket_name)['PublicAccessBlockConfiguration']
                if not all([pab.get('BlockPublicAcls', False), pab.get('IgnorePublicAcls', False), pab.get('BlockPublicPolicy', False), pab.get('RestrictPublicBuckets', False)]):
                    reasons.append("일부 퍼블릭 액세스 차단 비활성")
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchPublicAccessBlockConfiguration':
                    reasons.append("퍼블릭 액세스 차단 미설정")
            
            # 2. ACL 확인
            try:
                acl = s3.get_bucket_acl(Bucket=bucket_name)
                for grant in acl['Grants']:
                    if grant.get('Grantee', {}).get('URI') == 'http://acs.amazonaws.com/groups/global/AllUsers':
                        reasons.append("ACL로 전체 사용자에게 공개됨")
                        break
            except ClientError: pass
            
            # 3. Bucket Policy 확인
            try:
                policy_str = s3.get_bucket_policy(Bucket=bucket_name)['Policy']
                policy = json.loads(policy_str)
                for stmt in policy.get('Statement', []):
                    if stmt.get('Effect') == 'Allow':
                        principal = stmt.get('Principal')
                        if principal == '*' or (isinstance(principal, dict) and principal.get('AWS') == '*'):
                            reasons.append("버킷 정책으로 전체에 공개됨")
                            break
            except ClientError: pass

            if reasons:
                public_buckets_reasons[bucket_name] = reasons

        if not public_buckets_reasons:
            print("[✓ COMPLIANT] 3.7 공개적으로 액세스 가능한 S3 버킷이 없습니다.")
        else:
            print(f"[⚠ WARNING] 3.7 공개적으로 액세스 가능한 S3 버킷이 존재합니다 ({len(public_buckets_reasons)}개).")
            for bucket, reasons in public_buckets_reasons.items():
                print(f"  ├─ 버킷 '{bucket}' (사유: {', '.join(reasons)})")
            print("  └─ 🔧 S3 콘솔에서 [권한] > [퍼블릭 액세스 차단]을 모두 활성화하고, 버킷 정책 및 ACL을 검토하여 공개 설정을 제거하세요.")
            
    except ClientError as e:
        print(f"[ERROR] S3 버킷 정보를 가져오는 중 오류 발생: {e}")