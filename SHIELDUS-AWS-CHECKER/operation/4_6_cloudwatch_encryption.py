# 4.operation/4_6_cloudwatch_encryption.py
import boto3
import json
import datetime
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
        log_groups_found = False

        for page in paginator.paginate():
            if 'logGroups' in page and page['logGroups']:
                log_groups_found = True
                for group in page['logGroups']:
                    if 'kmsKeyId' not in group:
                        unencrypted_log_groups.append(group['logGroupName'])

        if not log_groups_found:
            print("[INFO] 4.6 CloudWatch 로그 그룹이 존재하지 않습니다.")
            return []

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
    - 미암호화 로그 그룹에 대해 KMS 암호화 적용
    """
    if not unencrypted_log_groups:
        return

    logs = boto3.client('logs')
    kms = boto3.client('kms')
    print("[FIX] 4.6 CloudWatch 로그 그룹 암호화 조치를 시작합니다.")

    try:
        key_arn = input("  -> 사용할 KMS Key ARN을 입력하세요 (새로 생성하려면 'new' 입력): ").strip()
        account_id = boto3.client('sts').get_caller_identity()['Account']
        region = boto3.session.Session().region_name

        if not key_arn:
            print("     [ERROR] KMS 키를 입력하지 않았습니다. 'new' 또는 alias/arn 형식으로 입력해야 합니다.")
            return

        if key_arn.lower() == 'new':
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            alias_name = f"alias/cloudwatch-autokey-{timestamp}"

            response = kms.create_key(
                Description=f'CloudWatch 로그 암호화를 위한 자동 생성 KMS 키 ({timestamp})',
                KeyUsage='ENCRYPT_DECRYPT',
                Origin='AWS_KMS'
            )
            key_id = response['KeyMetadata']['KeyId']
            key_arn = f"arn:aws:kms:{region}:{account_id}:key/{key_id}"

            policy = {
                "Version": "2012-10-17",
                "Id": "cloudwatch-access",
                "Statement": [
                    {
                        "Sid": "Allow CloudWatch Logs",
                        "Effect": "Allow",
                        "Principal": {
                            "Service": f"logs.{region}.amazonaws.com"
                        },
                        "Action": [
                            "kms:Encrypt",
                            "kms:Decrypt",
                            "kms:ReEncrypt*",
                            "kms:GenerateDataKey*",
                            "kms:DescribeKey"
                        ],
                        "Resource": "*",
                        "Condition": {
                            "ArnLike": {
                                "kms:EncryptionContext:aws:logs:arn": f"arn:aws:logs:{region}:{account_id}:*"
                            }
                        }
                    },
                    {
                        "Sid": "Allow Admin Full Access",
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": f"arn:aws:iam::{account_id}:root"
                        },
                        "Action": "kms:*",
                        "Resource": "*"
                    }
                ]
            }

            kms.put_key_policy(
                KeyId=key_id,
                PolicyName='default',
                Policy=json.dumps(policy)
            )

            kms.create_alias(AliasName=alias_name, TargetKeyId=key_id)
            print(f"     [INFO] 새로운 KMS 키를 생성했습니다.")
            print(f"     [INFO] 별칭: {alias_name}")
            print(f"     [INFO] Key ARN: {key_arn}")

        else:
            aliases = kms.list_aliases()['Aliases']
            alias_names = [a['AliasName'] for a in aliases if 'AliasName' in a]
            if key_arn.startswith("alias/"):
                if key_arn not in alias_names:
                    print(f"     [ERROR] 입력한 KMS alias '{key_arn}'를 찾을 수 없습니다.")
                    return
            elif key_arn.startswith("arn:"):
                try:
                    kms.describe_key(KeyId=key_arn)
                except ClientError:
                    print(f"     [ERROR] 입력한 KMS 키 ARN '{key_arn}'를 찾을 수 없습니다.")
                    return

        for group_name in unencrypted_log_groups:
            if input(f"  -> 로그 그룹 '{group_name}'에 KMS 암호화를 적용하시겠습니까? (y/n): ").lower() == 'y':
                try:
                    logs.associate_kms_key(logGroupName=group_name, kmsKeyId=key_arn)
                    print(f"     [SUCCESS] 로그 그룹 '{group_name}'에 KMS 키를 연결했습니다.")
                except ClientError as e:
                    print(f"     [ERROR] 로그 그룹 '{group_name}' 키 연결 실패: {e}")

    except ClientError as e:
        print(f"     [ERROR] KMS 키 생성 또는 설정 중 오류 발생: {e}")

if __name__ == "__main__":
    groups = check()
    fix(groups)