#  4.operation\4_10_s3_bucket_logging.py
import boto3
import time
from botocore.exceptions import ClientError

def check_cloudtrail_s3_buckets():
    ct = boto3.client('cloudtrail')
    try:
        trails = ct.describe_trails()['trailList']
        return list(set([t['S3BucketName'] for t in trails if 'S3BucketName' in t]))
    except ClientError as e:
        print(f"[ERROR] CloudTrail 설정 조회 실패: {e}")
        return []

def check_logging_enabled(bucket_name):
    s3 = boto3.client('s3')
    try:
        response = s3.get_bucket_logging(Bucket=bucket_name)
        return 'LoggingEnabled' in response
    except ClientError as e:
        print(f"[ERROR] '{bucket_name}'의 로깅 상태 확인 실패: {e}")
        return False

def create_log_bucket(region):
    s3 = boto3.client('s3')
    timestamp = time.strftime('%Y%m%d%H%M%S')
    bucket_name = f'cloudtrail-access-logs-{timestamp}'
    try:
        s3.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={'LocationConstraint': region}
        )
        print(f"[SUCCESS] 로그 저장용 버킷 '{bucket_name}'을 생성했습니다.")
        return bucket_name
    except ClientError as e:
        print(f"[ERROR] 버킷 생성 실패: {e}")
        return None

def enable_access_logging(source_bucket, target_bucket):
    s3 = boto3.client('s3')
    try:
        if source_bucket == target_bucket:
            print(f"[SKIP] '{source_bucket}' 버킷이 자기 자신을 대상으로 지정할 수 없습니다.")
            return
        s3.put_bucket_logging(
            Bucket=source_bucket,
            BucketLoggingStatus={
                'LoggingEnabled': {
                    'TargetBucket': target_bucket,
                    'TargetPrefix': f'{source_bucket}/'
                }
            }
        )
        print(f"[SUCCESS] '{source_bucket}'의 서버 액세스 로깅을 '{target_bucket}'으로 설정했습니다.")
    except ClientError as e:
        print(f"[ERROR] '{source_bucket}' 설정 실패: {e}")

def fix(buckets, region):
    if not buckets:
        return

    print("[FIX] 서버 액세스 로깅 미설정 버킷에 대한 조치를 시작합니다.")

    for bucket in buckets:
        if check_logging_enabled(bucket):
            continue
        print(f"\n[INFO] '{bucket}' 버킷은 서버 액세스 로깅이 설정되어 있지 않습니다.")
        confirm = input(f"  -> '{bucket}'에 대해 서버 액세스 로깅을 활성화하시겠습니까? (y/n): ").strip().lower()
        if confirm != 'y':
            continue

        method = input("     └─ 로그를 저장할 버킷을 입력하시겠습니까? (n 입력 시 자동 생성됨) (y/n): ").strip().lower()
        if method == 'y':
            target_bucket = input("     → 대상 버킷 이름 입력: ").strip()
        else:
            target_bucket = create_log_bucket(region)

        if not target_bucket:
            print(f"     [INFO] 대상 버킷이 준비되지 않아 '{bucket}'에 대한 조치를 건너뜁니다.")
            continue

        if bucket == target_bucket:
            print(f"     [SKIP] 자기 자신에게 로그를 저장할 수 없습니다. 건너뜁니다.")
            continue

        enable_access_logging(bucket, target_bucket)

def run():
    print("[INFO] 4.10 CloudTrail 로그 버킷의 서버 액세스 로깅 점검을 시작합니다.")
    ct_buckets = check_cloudtrail_s3_buckets()

    if not ct_buckets:
        print("[INFO] CloudTrail 로그 저장 버킷이 없습니다.")
        return

    insecure_buckets = []
    for bucket in ct_buckets:
        if not check_logging_enabled(bucket):
            insecure_buckets.append(bucket)

    if not insecure_buckets:
        print("[✓ COMPLIANT] 모든 CloudTrail 로그 버킷에 서버 액세스 로깅이 활성화되어 있습니다.")
        return

    print(f"[⚠ WARNING] 다음 버킷들은 서버 액세스 로깅이 설정되어 있지 않습니다 ({len(insecure_buckets)}개):")
    for b in insecure_buckets:
        print(f"  ├─ {b}")

    region = boto3.session.Session().region_name
    fix(insecure_buckets, region)

if __name__ == "__main__":
    run()