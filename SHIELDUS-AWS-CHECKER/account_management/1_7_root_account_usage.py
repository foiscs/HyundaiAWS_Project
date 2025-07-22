# 코드 수정 필요
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta, timezone
import json

def check():
    """
    [1.7] Admin Console 관리자 정책 관리
    - 최근 90일 간 루트 계정으로 수행된 서비스 이벤트들을 출력하고,
      수동 점검 참고자료로 제공
    """
    print("[INFO] 1.7 Admin Console 관리자 정책 관리 체크 중...")
    print("[ⓘ MANUAL] 이 항목은 루트 계정이 서비스 용도로 사용되는지 여부를 수동으로 판별해야 합니다.")

    cloudtrail = boto3.client('cloudtrail')
    lookback_days = 90
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(days=lookback_days)

    try:
        print(f"[INFO] 최근 {lookback_days}일 간 Root 계정 활동 내역을 조회합니다...")

        # Root 계정이 수행한 이벤트 목록 수집
        root_events = set()  # 중복 제거를 위해 set 사용
        paginator = cloudtrail.get_paginator('lookup_events')
        pages = paginator.paginate(
            LookupAttributes=[
                {'AttributeKey': 'Username', 'AttributeValue': 'Root'}
            ],
            StartTime=start_time,
            EndTime=now
        )

        for page in pages:
            for event in page['Events']:
                try:
                    cloudtrail_event = json.loads(event['CloudTrailEvent'])  
                    user_type = cloudtrail_event.get('userIdentity', {}).get('type', '')
                    if user_type == 'Root':
                        event_name = cloudtrail_event.get('eventName')
                        if event_name:
                            root_events.add(event_name)
                except Exception:
                    continue 

        if not root_events:
            print("[✓ COMPLIANT] 최근 루트 계정으로 수행된 서비스 관련 이벤트가 없습니다.")
        else:
            print(f"[⚠ 참고] 최근 루트 계정으로 수행된 서비스 이벤트 {len(root_events)}건:")
            for e in sorted(root_events):
                print(f"  ├─ {e}")

            print("\n[수동 판정 필요]")
            print("  └─ 위 이벤트 중 운영성 또는 서비스성 작업(예: RunInstances, PutObject 등)이 있다면 '서비스 용도 사용'으로 판단하세요.")

        return True

    except ClientError as e:
        print(f"[ERROR] CloudTrail 이벤트 조회 중 오류 발생: {e}")
        return False

if __name__ == "__main__":
    check()
