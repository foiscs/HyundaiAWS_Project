import boto3
from botocore.exceptions import ClientError
import json

def is_bucket_public(s3_client, bucket_name):
    """S3 버킷이 공개 상태인지 확인하는 헬퍼 함수"""
    # 1. Public Access Block이 모든 공개를 차단하는지 확인
    try:
        pab = s3_client.get_public_access_block(Bucket=bucket_name)['PublicAccessBlockConfiguration']
        if all([pab.get(key) for key in ['BlockPublicAcls', 'IgnorePublicAcls', 'BlockPublicPolicy', 'RestrictPublicBuckets']]):
            return False, ""  # 완전히 차단됨
    except ClientError as e:
        if e.response['Error']['Code'] != 'NoSuchPublicAccessBlockConfiguration':
            raise e
        # 설정이 없으면 공개 가능성이 있으므로 계속 확인

    # 2. 버킷 정책(Policy) 확인
    try:
        policy_str = s3_client.get_bucket_policy(Bucket=bucket_name)['Policy']
        policy = json.loads(policy_str)
        for stmt in policy.get('Statement', []):
            principal = stmt.get('Principal')
            if stmt.get('Effect') == 'Allow' and (principal == '*' or (isinstance(principal, dict) and principal.get('AWS') == '*')):
                return True, "버킷 정책으로 전체 공개"
    except ClientError: pass

    # 3. ACL 확인
    try:
        acl = s3_client.get_bucket_acl(Bucket=bucket_name)
        for grant in acl['Grants']:
            if grant.get('Grantee', {}).get('URI') == 'http://acs.amazonaws.com/groups/global/AllUsers':
                return True, "ACL로 전체 사용자에게 공개"
    except ClientError: pass

    return False, ""

def check():
    """
    [3.7] S3 버킷/객체 접근 관리
    - 공개된 S3 버킷을 점검하고, 해당 버킷 목록과 사유를 반환
    """
    print("[INFO] 3.7 S3 버킷/객체 접근 관리 체크 중...")
    s3 = boto3.client('s3')
    public_buckets = {}
    
    try:
        for bucket in s3.list_buckets()['Buckets']:
            bucket_name = bucket['Name']
            is_public, reason = is_bucket_public(s3, bucket_name)
            if is_public:
                public_buckets[bucket_name] = reason

        if not public_buckets:
            print("[✓ COMPLIANT] 3.7 공개적으로 액세스 가능한 S3 버킷이 없습니다.")
        else:
            print(f"[⚠ WARNING] 3.7 공개적으로 액세스 가능한 S3 버킷이 존재합니다 ({len(public_buckets)}개).")
            for bucket, reason in public_buckets.items():
                print(f"  ├─ 공개 버킷: '{bucket}' (사유: {reason})")
        
        return list(public_buckets.keys())
            
    except ClientError as e:
        print(f"[ERROR] S3 버킷 정보를 가져오는 중 오류 발생: {e}")
        return []

def fix(public_buckets):
    """
    [3.7] S3 버킷/객체 접근 관리 조치
    - 공개된 버킷에 대해 퍼블릭 액세스 차단을 적용
    """
    if not public_buckets:
        return

    s3 = boto3.client('s3')
    print("[FIX] 3.7 공개된 S3 버킷에 대한 조치를 시작합니다.")
    for bucket_name in public_buckets:
        choice = input(f"  -> 버킷 '{bucket_name}'에 모든 퍼블릭 액세스 차단을 적용하시겠습니까? (정적 웹사이트 호스팅 시 서비스에 영향) (y/n): ").lower()
        if choice == 'y':
            try:
                s3.put_public_access_block(
                    Bucket=bucket_name,
                    PublicAccessBlockConfiguration={
                        'BlockPublicAcls': True, 'IgnorePublicAcls': True,
                        'BlockPublicPolicy': True, 'RestrictPublicBuckets': True
                    }
                )
                print(f"     [SUCCESS] 버킷 '{bucket_name}'의 퍼블릭 액세스를 차단했습니다.")
            except ClientError as e:
                print(f"     [ERROR] 퍼블릭 액세스 차단 실패: {e}")
        else:
            print(f"     [INFO] 버킷 '{bucket_name}' 조치를 건너뜁니다.")

if __name__ == "__main__":
    bucket_list = check()
    fix(bucket_list)