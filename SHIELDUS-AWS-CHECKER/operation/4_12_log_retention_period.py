#  4.operation/4_12_log_retention_period.py
import boto3
from botocore.exceptions import ClientError

def check():
    """
    [4.12] CloudWatch 로그 보관 기간 설정 점검
    - 주요 로그 그룹의 보관 기간이 1년(365일) 이상으로 설정되어 있는지 확인
    - 설정이 없거나 365일 미만이면 취약
    """
    print("[INFO] 4.12 주요 CloudWatch 로그 그룹의 보관 기간 점검 중...")
    logs = boto3.client('logs')
    short_retention_groups = []

    # 주요 키워드 (가이드 기준)
    target_keywords = ['cloudtrail', 'vpc-flow-logs', 'vpc/flowlogs', 'rds', 's3', 'efs', 'ebs', 'fsx', 'dynamodb']

    try:
        paginator = logs.get_paginator('describe_log_groups')
        for page in paginator.paginate():
            for group in page['logGroups']:
                name = group['logGroupName'].lower()
                if any(keyword in name for keyword in target_keywords):
                    retention = group.get('retentionInDays')
                    if retention is None or retention < 365:
                        short_retention_groups.append({
                            'name': group['logGroupName'],
                            'days': retention if retention is not None else '무제한'
                        })

        if not short_retention_groups:
            print("[✓ COMPLIANT] 4.12 모든 주요 로그 그룹의 보관 기간이 1년 이상으로 설정되어 있습니다.")
        else:
            print(f"[⚠ WARNING] 4.12 보관 기간이 1년 미만이거나 설정되지 않은 주요 로그 그룹이 있습니다 ({len(short_retention_groups)}개).")
            for f in short_retention_groups:
                print(f"  ├─ {f['name']} (보관 기간: {f['days']}일)")

        return short_retention_groups

    except ClientError as e:
        print(f"[ERROR] CloudWatch 로그 그룹 정보를 가져오는 중 오류 발생: {e}")
        return []

def fix(short_retention_groups):
    """
    [4.12] 로그 보관 기간 조치
    - 보관 기간이 짧거나 설정되지 않은 그룹의 보관 기간을 365일로 수정
    """
    if not short_retention_groups:
        return

    logs = boto3.client('logs')
    print("[FIX] 4.12 로그 그룹 보관 기간 설정 조치를 시작합니다.")
    for group in short_retention_groups:
        group_name = group['name']
        display_days = f"{group['days']}일" if isinstance(group['days'], int) else "무제한(설정되지 않음)"
        if input(f"  -> 로그 그룹 '{group_name}' (현재 보존 기간: {display_days})의 보존 기간을 365일로 설정하시겠습니까? (y/n): ").lower() == 'y':
            try:
                logs.put_retention_policy(logGroupName=group_name, retentionInDays=365)
                print(f"     [SUCCESS] '{group_name}'의 보존 기간을 365일로 설정했습니다.")
            except ClientError as e:
                print(f"     [ERROR] 설정 실패: {e}")

if __name__ == "__main__":
    groups = check()
    fix(groups)
