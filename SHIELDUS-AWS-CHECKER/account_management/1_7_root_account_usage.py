import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta, timezone
import json

def check():
    """
    [1.7] Admin Console(Root) 관리자 정책 관리
    - 최근 루트 계정으로 AWS Console 로그인 이벤트가 있었는지 확인하여,
      루트 계정을 일상적인 작업에 사용하는지 자동 점검
    """
    print("[INFO] 1.7 Admin Console(Root) 관리자 정책 관리 체크 중...")

    cloudtrail = boto3.client('cloudtrail')
    lookback_days = 90  # 최근 90일 기준
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(days=lookback_days)

    try:
        print(f"[INFO] 최근 {lookback_days}일 간 Root 로그인 이벤트를 조회합니다...")

        events = cloudtrail.lookup_events(
            LookupAttributes=[
                {'AttributeKey': 'EventName', 'AttributeValue': 'ConsoleLogin'}
            ],
            StartTime=start_time,
            EndTime=now,
            MaxResults=50
        )

        root_login_detected = False

        for event in events['Events']:
            cloudtrail_event = json.loads(event['CloudTrailEvent'])
            print(cloudtrail_event)
            user_type = cloudtrail_event.get('userIdentity', {}).get('type', '')
            if user_type == 'Root':
                root_login_detected = True
                login_time = event['EventTime']
                print(f"[⚠ WARNING] 루트 계정으로 AWS 콘솔 로그인이 감지되었습니다. (시간: {login_time})")
                break

        if not root_login_detected:
            print("[✓ COMPLIANT] 최근 루트 계정으로의 콘솔 로그인 이력이 없습니다.")
        else:
            print("  └─ 루트 계정은 긴급 상황 외에 사용하지 말고, 반드시 MFA를 활성화한 상태로 제한하세요.")

        return not root_login_detected

    except ClientError as e:
        print(f"[ERROR] CloudTrail 이벤트 조회 중 오류 발생: {e}")
        return False
if __name__ == "__main__":
    check()