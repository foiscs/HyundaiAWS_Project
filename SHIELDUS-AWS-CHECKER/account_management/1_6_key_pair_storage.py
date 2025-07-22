import boto3
from botocore.exceptions import ClientError
import json

def is_bucket_public(s3_client, bucket_name):
    try:
        pab = s3_client.get_public_access_block(Bucket=bucket_name)['PublicAccessBlockConfiguration']
        if all([pab.get('BlockPublicAcls'), pab.get('IgnorePublicAcls'), pab.get('BlockPublicPolicy'), pab.get('RestrictPublicBuckets')]):
            return False
    except ClientError as e:
        if e.response['Error']['Code'] != 'NoSuchPublicAccessBlockConfiguration':
            raise e
    try:
        policy_status = s3_client.get_bucket_policy_status(Bucket=bucket_name)
        if policy_status['PolicyStatus']['IsPublic']:
            return True
    except ClientError: pass
    try:
        acl = s3_client.get_bucket_acl(Bucket=bucket_name)
        for grant in acl['Grants']:
            if grant.get('Grantee', {}).get('URI') == 'http://acs.amazonaws.com/groups/global/AllUsers':
                return True
    except ClientError: pass
    return False

def check():
    """
    [1.6] Key Pair 보관 관리
    - 공개 가능한 S3 버킷에 Key Pair(.pem) 파일이 저장되어 있는지 점검하고, 해당 파일 목록 반환
    """
    print("[INFO] 1.6 Key Pair 보관 관리 체크 중...")
    s3 = boto3.client('s3')
    vulnerable_keys = {}

    try:
        for bucket in s3.list_buckets()['Buckets']:
            bucket_name = bucket['Name']
            if is_bucket_public(s3, bucket_name):
                try:
                    paginator = s3.get_paginator('list_objects_v2')
                    for page in paginator.paginate(Bucket=bucket_name):
                        for obj in page.get('Contents', []):
                            if obj['Key'].lower().endswith('.pem'):
                                if bucket_name not in vulnerable_keys:
                                    vulnerable_keys[bucket_name] = []
                                vulnerable_keys[bucket_name].append(obj['Key'])
                except ClientError: pass

        if not vulnerable_keys:
            print("[✓ COMPLIANT] 1.6 공개 가능한 S3 버킷에서 Key Pair 파일이 발견되지 않았습니다.")
        else:
            print(f"[⚠ WARNING] 1.6 공개 가능한 S3 버킷에 Key Pair 파일(.pem)이 존재합니다 ({sum(len(v) for v in vulnerable_keys.values())}개).")
            for bucket, keys in vulnerable_keys.items():
                print(f"  ├─ 버킷 '{bucket}': {', '.join(keys)}")
        
        return vulnerable_keys

    except ClientError as e:
        print(f"[ERROR] S3 버킷 정보를 가져오는 중 오류 발생: {e}")
        return {}

def fix(vulnerable_keys):
    """
    [1.6] Key Pair 보관 관리 조치
    - 공개된 버킷의 .pem 파일을 삭제하거나 버킷 자체를 비공개로 전환
    """
    if not vulnerable_keys:
        return
        
    s3 = boto3.client('s3')
    print("[FIX] 1.6 공개된 S3 버킷의 Key Pair 파일에 대한 조치를 시작합니다.")
    for bucket_name, keys in vulnerable_keys.items():
        choice = input(f"  -> 버킷 '{bucket_name}'에 대한 조치를 선택하세요 ([D]elete keys, [P]rivatize bucket, [i]gnore): ").lower()
        if choice == 'd':
            objects_to_delete = [{'Key': key} for key in keys]
            confirm = input(f"     정말로 버킷 '{bucket_name}'에서 {len(keys)}개의 .pem 파일을 삭제하시겠습니까? (yes/no): ").lower()
            if confirm == 'yes':
                try:
                    s3.delete_objects(Bucket=bucket_name, Delete={'Objects': objects_to_delete})
                    print(f"     [SUCCESS] {len(keys)}개의 키 파일을 삭제했습니다.")
                except ClientError as e:
                    print(f"     [ERROR] 키 파일 삭제 실패: {e}")
        elif choice == 'p':
            confirm = input(f"     정말로 버킷 '{bucket_name}'의 모든 퍼블릭 액세스를 차단하시겠습니까? (yes/no): ").lower()
            if confirm == 'yes':
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
            print(f"     [INFO] 버킷 '{bucket_name}'에 대한 조치를 건너뜁니다.")

if __name__ == "__main__":
    key_list = check()
    fix(key_list)