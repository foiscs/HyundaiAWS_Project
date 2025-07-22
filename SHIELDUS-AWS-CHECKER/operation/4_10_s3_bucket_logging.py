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
        for bucket in s3.list_buckets()['Buckets']:
            bucket_name = bucket['Name']
            try:
                if 'LoggingEnabled' not in s3.get_bucket_logging(Bucket=bucket_name):
                    logging_disabled_buckets.append(bucket_name)
            except ClientError as e:
                print(f"[ERROR] 버킷 '{bucket_name}'의 로깅 정보 확인 중 오류: {e}")
        
        if not logging_disabled_buckets:
            print("[✓ COMPLIANT] 4.10 모든 S3 버킷에 서버 액세스 로깅이 활성화되어 있습니다.")
        else:
            print(f"[⚠ WARNING] 4.10 서버 액세스 로깅이 비활성화된 S3 버킷이 존재합니다 ({len(logging_disabled_buckets)}개).")
            print(f"  ├─ 해당 버킷: {', '.join(logging_disabled_buckets)}")
        
        return logging_disabled_buckets

    except ClientError as e:
        print(f"[ERROR] S3 버킷 목록을 가져오는 중 오류 발생: {e}")
        return []

def fix(logging_disabled_buckets):
    """
    [4.10] S3 버킷 로깅 설정 조치
    - 서버 액세스 로깅을 활성화
    """
    if not logging_disabled_buckets: return

    s3 = boto3.client('s3')
    print("[FIX] 4.10 S3 서버 액세스 로깅 조치를 시작합니다.")
    target_bucket = input("  -> 로그를 저장할 대상 버킷 이름을 입력하세요 (없으면 Enter 눌러 건너뛰기): ").strip()
    if not target_bucket:
        print("     [INFO] 대상 버킷이 없어 조치를 건너뜁니다.")
        return

    for bucket_name in logging_disabled_buckets:
        if bucket_name == target_bucket: continue # 자기 자신에게 로깅 불가
        if input(f"  -> 버킷 '{bucket_name}'의 로그를 '{target_bucket}'에 저장하시겠습니까? (y/n): ").lower() == 'y':
            try:
                s3.put_bucket_logging(
                    Bucket=bucket_name,
                    BucketLoggingStatus={
                        'LoggingEnabled': {'TargetBucket': target_bucket, 'TargetPrefix': f'{bucket_name}/'}
                    }
                )
                print(f"     [SUCCESS] 버킷 '{bucket_name}'의 로깅을 활성화했습니다.")
            except ClientError as e:
                print(f"     [ERROR] 로깅 활성화 실패: {e}")

if __name__ == "__main__":
    buckets = check()
    fix(buckets)