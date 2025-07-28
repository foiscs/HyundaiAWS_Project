#  4.operation/4_7_user_access_logging.py
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timezone
import json

def check():
    """
    [4.7] AWS 사용자 계정 접근 로깅 설정
    - 멀티 리전 + 관리 이벤트 포함한 CloudTrail 추적이 하나라도 존재하는지 점검
    """
    print("[INFO] 4.7 사용자 계정 접근 로깅 설정 체크 중...")
    cloudtrail = boto3.client('cloudtrail')
    trails_with_mgmt_events = []

    try:
        trails = cloudtrail.describe_trails()['trailList']
        for trail in trails:
            name = trail['Name']
            is_multi = trail.get('IsMultiRegionTrail')
            is_logging = cloudtrail.get_trail_status(Name=name).get('IsLogging')

            try:
                selectors = cloudtrail.get_event_selectors(TrailName=name).get('EventSelectors', [])
                has_mgmt = any(sel.get('IncludeManagementEvents') for sel in selectors)
            except:
                has_mgmt = False

            if is_multi and is_logging and has_mgmt:
                trails_with_mgmt_events.append(name)

        if trails_with_mgmt_events:
            print("[✓ COMPLIANT] 4.7 조건을 만족하는 CloudTrail 추적이 존재합니다.")
            for t in trails_with_mgmt_events:
                print(f"  ├─ {t}")
            return True
        else:
            print("[⚠ WARNING] 4.7 조건을 만족하는 CloudTrail이 존재하지 않습니다.")
            return False

    except ClientError as e:
        print(f"[ERROR] CloudTrail 조회 중 오류 발생: {e}")
        return False


def fix():
    """
    [4.7] AWS 사용자 계정 접근 로깅 설정 조치
    - 멀티 리전 + 관리 이벤트 포함 CloudTrail 자동 생성
    - S3 버킷도 함께 생성 (timestamp 포함 이름), 정책 포함
    """
    cloudtrail = boto3.client('cloudtrail')
    s3 = boto3.client('s3')
    sts = boto3.client('sts')

    account_id = sts.get_caller_identity()['Account']
    region = boto3.session.Session().region_name
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')

    trail_name = f'project2-management-trail-{timestamp}'
    bucket_name = f'cloudtrail-logs-project2-{timestamp}'

    print(f"[INFO] S3 버킷 생성 중: {bucket_name}")
    try:
        s3.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={'LocationConstraint': region}
        )
        print("  └─ 생성 완료")

        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AWSCloudTrailAclCheck",
                    "Effect": "Allow",
                    "Principal": {"Service": "cloudtrail.amazonaws.com"},
                    "Action": "s3:GetBucketAcl",
                    "Resource": f"arn:aws:s3:::{bucket_name}"
                },
                {
                    "Sid": "AWSCloudTrailWrite",
                    "Effect": "Allow",
                    "Principal": {"Service": "cloudtrail.amazonaws.com"},
                    "Action": "s3:PutObject",
                    "Resource": f"arn:aws:s3:::{bucket_name}/AWSLogs/{account_id}/*",
                    "Condition": {
                        "StringEquals": {
                            "s3:x-amz-acl": "bucket-owner-full-control"
                        }
                    }
                }
            ]
        }

        s3.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(policy))
        print("  └─ S3 버킷 정책 설정 완료")

    except ClientError as e:
        print(f"  └─ [ERROR] S3 버킷 생성 또는 정책 설정 실패: {e}")
        return

    try:
        print(f"[INFO] CloudTrail 추적 생성 중: {trail_name}")
        cloudtrail.create_trail(
            Name=trail_name,
            S3BucketName=bucket_name,
            IsMultiRegionTrail=True,
            IncludeGlobalServiceEvents=True
        )

        cloudtrail.start_logging(Name=trail_name)

        cloudtrail.put_event_selectors(
            TrailName=trail_name,
            EventSelectors=[{
                'ReadWriteType': 'All',
                'IncludeManagementEvents': True,
                'DataResources': []
            }]
        )

        print(f"[SUCCESS] 멀티 리전 CloudTrail '{trail_name}' 생성 완료 (관리 이벤트 포함)")
    except ClientError as e:
        print(f"[ERROR] CloudTrail 생성 실패: {e}")


if __name__ == "__main__":
    if not check():
        fix()
