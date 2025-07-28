#  4.operation/4_5_cloudtrail_encryption.py
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
        account_id = boto3.client('sts').get_caller_identity()['Account']
        region = boto3.session.Session().region_name
        alias_name = "alias/cloudtrail-autokey"
        key_arn = None

        # 1. 먼저 기존 alias 존재 여부 확인
        existing_aliases = kms.list_aliases()['Aliases']
        alias_dict = {a['AliasName']: a['TargetKeyId'] for a in existing_aliases if 'AliasName' in a and 'TargetKeyId' in a}

        if alias_name in alias_dict:
            print(f"[INFO] KMS 별칭 '{alias_name}'이 이미 존재합니다.")
            use = input("  → 해당 키를 사용하시겠습니까? (y/n): ").strip().lower()
            if use == 'y':
                key_id = alias_dict[alias_name]
                key_arn = f"arn:aws:kms:{region}:{account_id}:key/{key_id}"
                print(f"[INFO] 기존 키 ARN 사용: {key_arn}")
            else:
                key_arn = input("  -> 사용할 KMS Key ARN을 입력하세요 (새로 생성하려면 'new' 입력): ").strip()
        else:
            key_arn = input("  -> 사용할 KMS Key ARN을 입력하세요 (새로 생성하려면 'new' 입력): ").strip()

        # 2. 입력된 값 처리
        if not key_arn:
            print("     [ERROR] KMS 키를 입력하지 않았습니다. fix()를 다시 실행해주세요.")
            return

        if key_arn.lower() == 'new':
            print(f"[INFO] 별칭 '{alias_name}'로 새 KMS 키를 생성합니다.")
            response = kms.create_key(
                Description='CloudTrail 암호화를 위한 자동 생성 KMS 키',
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
            print(f"[SUCCESS] 새 KMS 키 생성 완료")
            print(f"[INFO] 별칭: {alias_name}")
            print(f"[INFO] Key ARN: {key_arn}")

        elif key_arn.startswith("alias/"):
            alias_match = [a for a in existing_aliases if a.get('AliasName') == key_arn]
            if not alias_match:
                print(f"[ERROR] 입력한 alias '{key_arn}'를 찾을 수 없습니다.")
                return
            key_id = alias_match[0]['TargetKeyId']
            key_arn = f"arn:aws:kms:{region}:{account_id}:key/{key_id}"
            print(f"[INFO] 입력한 별칭 alias를 기반으로 키 ARN 해석 완료: {key_arn}")

        elif key_arn.startswith("arn:"):
            try:
                kms.describe_key(KeyId=key_arn)
            except ClientError:
                print(f"[ERROR] 입력한 KMS 키 ARN '{key_arn}'를 찾을 수 없습니다.")
                return

        # 3. 암호화 적용
        for trail_name in not_kms_encrypted_trails:
            if input(f"  -> Trail '{trail_name}'에 KMS 암호화를 적용하시겠습니까? (y/n): ").lower() == 'y':
                try:
                    cloudtrail.update_trail(Name=trail_name, KmsKeyId=key_arn)
                    print(f"     [SUCCESS] Trail '{trail_name}'에 KMS 암호화를 적용했습니다.")
                except ClientError as e:
                    print(f"     [ERROR] Trail '{trail_name}' 암호화 적용 실패: {e}")

    except ClientError as e:
        print(f"[ERROR] KMS 키 생성 또는 설정 중 오류 발생: {e}")


if __name__ == "__main__":
    trails = check()
    fix(trails)
