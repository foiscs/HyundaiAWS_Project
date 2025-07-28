#  4.operation/4_3_s3_encryption.py
import boto3
from botocore.exceptions import ClientError

def check():
    """
    [4.3] S3 암호화 설정
    - S3 버킷에 기본 암호화가 설정되어 있는지 점검하고, 미설정 버킷 목록을 반환
    """
    print("[INFO] 4.3 S3 암호화 설정 체크 중...")
    s3 = boto3.client('s3')
    unencrypted_buckets = []

    try:
        buckets = s3.list_buckets()['Buckets']
        if not buckets:
            print("[✓ INFO] 4.3 점검할 S3 버킷이 존재하지 않습니다.")
            return []
        
        for bucket in buckets:
            bucket_name = bucket['Name']
            try:
                s3.get_bucket_encryption(Bucket=bucket_name)
            except ClientError as e:
                if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                    unencrypted_buckets.append(bucket_name)
        
        if not unencrypted_buckets:
            print("[✓ COMPLIANT] 4.3 모든 S3 버킷에 기본 암호화가 설정되어 있습니다.")
        else:
            print(f"[⚠ WARNING] 4.3 기본 암호화가 설정되지 않은 S3 버킷이 존재합니다 ({len(unencrypted_buckets)}개).")
            print(f"  ├─ 해당 버킷: {', '.join(unencrypted_buckets)}")
        
        return unencrypted_buckets

    except ClientError as e:
        print(f"[ERROR] S3 버킷 목록을 가져오는 중 오류 발생: {e}")
        return []

def fix(unencrypted_buckets):
    """
    [4.3] S3 암호화 설정 조치
    - 기본 암호화가 없는 버킷에 SSE-S3 암호화를 적용
    """
    if not unencrypted_buckets: return

    s3 = boto3.client('s3')
    print("[FIX] 4.3 기본 암호화가 없는 S3 버킷에 대한 조치를 시작합니다.")
    for bucket_name in unencrypted_buckets:
        if input(f"  -> 버킷 '{bucket_name}'에 기본 암호화(SSE-S3)를 적용하시겠습니까? (y/n): ").lower() == 'y':
            try:
                s3.put_bucket_encryption(
                    Bucket=bucket_name,
                    ServerSideEncryptionConfiguration={'Rules': [{'ApplyServerSideEncryptionByDefault': {'SSEAlgorithm': 'AES256'}}]}
                )
                print(f"     [SUCCESS] 버킷 '{bucket_name}'에 SSE-S3 기본 암호화를 적용했습니다.")
            except ClientError as e:
                print(f"     [ERROR] 암호화 적용 실패: {e}")

if __name__ == "__main__":
    buckets = check()
    fix(buckets)