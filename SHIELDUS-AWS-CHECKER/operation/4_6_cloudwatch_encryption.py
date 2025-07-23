# 4.operation/4_6_cloudwatch_encryption.py
import boto3
from botocore.exceptions import ClientError

def check():
    """
    [4.6] CloudWatch 암호화 설정
    - CloudWatch Logs 로그 그룹이 KMS로 암호화되었는지 점검하고 미암호화 그룹 목록 반환
    """
    print("[INFO] 4.6 CloudWatch 암호화 설정 체크 중...")
    logs = boto3.client('logs')
    unencrypted_log_groups = []

    try:
        paginator = logs.get_paginator('describe_log_groups')
        for page in paginator.paginate():
            for group in page['logGroups']:
                if 'kmsKeyId' not in group:
                    unencrypted_log_groups.append(group['logGroupName'])

        if not unencrypted_log_groups:
            print("[✓ COMPLIANT] 4.6 모든 CloudWatch 로그 그룹이 KMS로 암호화되어 있습니다.")
        else:
            print(f"[⚠ WARNING] 4.6 KMS 암호화가 적용되지 않은 CloudWatch 로그 그룹이 존재합니다 ({len(unencrypted_log_groups)}개).")
            for group_name in unencrypted_log_groups[:5]: print(f"  ├─ {group_name}")
            if len(unencrypted_log_groups) > 5: print(f"  └─ ... 외 {len(unencrypted_log_groups) - 5}개 더 있음")
        
        return unencrypted_log_groups

    except ClientError as e:
        print(f"[ERROR] CloudWatch 로그 그룹 정보를 가져오는 중 오류 발생: {e}")
        return []

def fix(unencrypted_log_groups):
    """
    [4.6] CloudWatch 암호화 설정 조치
    - 미암호화 로그 그룹에 KMS 암호화 적용
    """
    if not unencrypted_log_groups: return

    logs = boto3.client('logs')
    print("[FIX] 4.6 CloudWatch 로그 그룹 암호화 조치를 시작합니다.")
    key_arn = input("  -> 사용할 KMS Key ARN을 입력하세요 (기본값을 사용하려면 Enter): ").strip()
    if not key_arn:
        account_id = boto3.client('sts').get_caller_identity()['Account']
        region = boto3.session.Session().region_name
        key_arn = f"arn:aws:kms:{region}:{account_id}:key/aws/logs" # CloudWatch Logs의 기본 키 별칭
        print(f"     [INFO] 기본 KMS 키(aws/logs)를 사용합니다. 키가 없다면 생성됩니다.")
    
    for group_name in unencrypted_log_groups:
        if input(f"  -> 로그 그룹 '{group_name}'에 KMS 암호화를 적용하시겠습니까? (y/n): ").lower() == 'y':
            try:
                logs.associate_kms_key(logGroupName=group_name, kmsKeyId=key_arn)
                print(f"     [SUCCESS] 로그 그룹 '{group_name}'에 KMS 키를 연결했습니다.")
            except ClientError as e:
                print(f"     [ERROR] 키 연결 실패: {e}")

if __name__ == "__main__":
    groups = check()
    fix(groups)