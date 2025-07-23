import boto3
from botocore.exceptions import ClientError

def check():
    """
    [4.12] 로그 보관 기간 설정
    - 주요 CloudWatch 로그 그룹의 보관 기간이 1년(365일) 이상으로 설정되었는지 점검
    """
    print("[INFO] 4.12 로그 보관 기간 설정 체크 중...")
    logs = boto3.client('logs')
    short_retention_groups = []

    try:
        paginator = logs.get_paginator('describe_log_groups')
        for page in paginator.paginate():
            for group in page['logGroups']:
                if 'CloudTrail' in group['logGroupName'] or 'vpc-flow-logs' in group['logGroupName']:
                    if group.get('retentionInDays', float('inf')) < 365:
                         short_retention_groups.append({'name': group['logGroupName'], 'days': group.get('retentionInDays', '영구')})

        if not short_retention_groups:
            print("[✓ COMPLIANT] 4.12 주요 로그 그룹의 보관 기간이 1년 이상으로 적절히 설정되어 있습니다.")
        else:
            print(f"[⚠ WARNING] 4.12 보관 기간이 1년 미만인 주요 로그 그룹이 있습니다 ({len(short_retention_groups)}개).")
            for f in short_retention_groups: print(f"  ├─ {f['name']} (보관 기간: {f['days']}일)")
        
        return short_retention_groups

    except ClientError as e:
        print(f"[ERROR] CloudWatch 로그 그룹 정보를 가져오는 중 오류 발생: {e}")
        return []

def fix(short_retention_groups):
    """
    [4.12] 로그 보관 기간 설정 조치
    - 보관 기간이 짧은 그룹의 기간을 365일로 설정
    """
    if not short_retention_groups: return

    logs = boto3.client('logs')
    print("[FIX] 4.12 로그 그룹 보관 기간 설정 조치를 시작합니다.")
    for group in short_retention_groups:
        group_name = group['name']
        if input(f"  -> 로그 그룹 '{group_name}'의 보관 기간을 365일로 설정하시겠습니까? (y/n): ").lower() == 'y':
            try:
                logs.put_retention_policy(logGroupName=group_name, retentionInDays=365)
                print(f"     [SUCCESS] '{group_name}'의 보관 기간을 365일로 설정했습니다.")
            except ClientError as e:
                print(f"     [ERROR] 설정 실패: {e}")

if __name__ == "__main__":
    groups = check()
    fix(groups)