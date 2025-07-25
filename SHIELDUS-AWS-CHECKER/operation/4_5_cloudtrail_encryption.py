# 4.operation/4_5_cloudtrail_encryption.py
import boto3
import json
import datetime
from botocore.exceptions import ClientError


def check():
    """
    [4.5] CloudTrail 암호화 설정
    - CloudTrail 로그 파일 암호화에 SSE-KMS가 사용되는지 점검하고, 미적용된 Trail 목록 반환
    """
    print("[INFO] 4.5 CloudTrail 암호화 설정 체크 중...")
    cloudtrail = boto3.client('cloudtrail')
    not_kms_encrypted_trails = []

    try:
        trails = cloudtrail.describe_trails().get('trailList', [])
        if not trails:
            print("[INFO] 4.5 활성화된 CloudTrail이 없습니다.")
            return []

        for trail in trails:
            if not trail.get('KmsKeyId'):
                not_kms_encrypted_trails.append(trail['Name'])

        if not not_kms_encrypted_trails:
            print("[✓ COMPLIANT] 4.5 모든 CloudTrail이 SSE-KMS로 암호화되어 있습니다.")
        else:
            print(f"[⚠ WARNING] 4.5 SSE-KMS 암호화가 적용되지 않은 CloudTrail이 존재합니다 ({len(not_kms_encrypted_trails)}개).")
            for group_name in not_kms_encrypted_trails[:5]: print(f"  ├─ {group_name}")
            if len(not_kms_encrypted_trails) > 5: print(f"  └─ ... 외 {len(not_kms_encrypted_trails) - 5}개 더 있음")

        return not_kms_encrypted_trails

    except ClientError as e:
        print(f"[ERROR] CloudTrail 정보를 가져오는 중 오류 발생: {e}")
        return []


def fix(not_kms_encrypted_trails):
    """
    [4.5] CloudTrail 암호화 설정 조치
    - KMS 암호화가 없는 Trail에 대해 사용자 확인 후 KMS 암호화 적용
    """
    if not not_kms_encrypted_trails:
        return

    cloudtrail = boto3.client('cloudtrail')
    kms = boto3.client('kms')
    print("[FIX] 4.5 CloudTrail SSE-KMS 암호화 조치를 시작합니다.")

    try:
        key_arn = input("  -> 사용할 KMS Key ARN을 입력하세요 (새로 생성하려면 'new' 입력): ").strip()
        if not key_arn:
            print("     [ERROR] KMS 키를 입력하지 않았습니다. 'new' 또는 alias/arn 형식으로 입력해야 합니다.")
            return
        account_id = boto3.client('sts').get_caller_identity()['Account']
        region = boto3.session.Session().region_name

        if key_arn.lower() == 'new':
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            alias_name = f"alias/cloudtrail-autokey-{timestamp}"

            response = kms.create_key(
                Description=f'CloudTrail 암호화를 위한 자동 생성 KMS 키 ({timestamp})',
                KeyUsage='ENCRYPT_DECRYPT',
                Origin='AWS_KMS'
            )
            key_id = response['KeyMetadata']['KeyId']
            key_arn = f"arn:aws:kms:{region}:{account_id}:key/{key_id}"

            policy = {
                "Version": "2012-10-17",
                "Id": "cloudtrail-access",
                "Statement": [
                    {
                        "Sid": "Allow CloudTrail",
                        "Effect": "Allow",
                        "Principal": { "Service": "cloudtrail.amazonaws.com" },
                        "Action": ["kms:GenerateDataKey*", "kms:Decrypt"],
                        "Resource": "*"
                    },
                    {
                        "Sid": "Allow Admin",
                        "Effect": "Allow",
                        "Principal": { "AWS": f"arn:aws:iam::{account_id}:root" },
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
            # 입력된 키가 실제 존재하는지 확인
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

        for trail_name in not_kms_encrypted_trails:
            if input(f"  -> Trail '{trail_name}'에 KMS 암호화를 적용하시겠습니까? (y/n): ").lower() == 'y':
                try:
                    cloudtrail.update_trail(Name=trail_name, KmsKeyId=key_arn)
                    print(f"     [SUCCESS] Trail '{trail_name}'에 KMS 암호화를 적용했습니다.")
                except ClientError as e:
                    print(f"     [ERROR] Trail '{trail_name}' 암호화 적용 실패: {e}")

    except ClientError as e:
        print(f"     [ERROR] KMS 키 생성 또는 설정 중 오류 발생: {e}")


if __name__ == "__main__":
    trails = check()
    fix(trails)
