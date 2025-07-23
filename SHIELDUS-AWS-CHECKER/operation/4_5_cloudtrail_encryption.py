# 4.operation/4_5_cloudtrail_encryption.py
import boto3
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
            # SSE-S3는 기본값이므로, KmsKeyId가 없는 경우 KMS 암호화 미적용으로 판단
            if not trail.get('KmsKeyId'):
                not_kms_encrypted_trails.append(trail['Name'])
        
        if not not_kms_encrypted_trails:
            print("[✓ COMPLIANT] 4.5 모든 CloudTrail이 SSE-KMS로 암호화되어 있습니다.")
        else:
            print(f"[⚠ WARNING] 4.5 SSE-KMS 암호화가 적용되지 않은 CloudTrail이 존재합니다 ({len(not_kms_encrypted_trails)}개).")
            print(f"  ├─ 해당 Trail: {', '.join(not_kms_encrypted_trails)}")
        
        return not_kms_encrypted_trails
    
    except ClientError as e:
        print(f"[ERROR] CloudTrail 정보를 가져오는 중 오류 발생: {e}")
        return []

def fix(not_kms_encrypted_trails):
    """
    [4.5] CloudTrail 암호화 설정 조치
    - KMS 암호화가 없는 Trail에 대해 사용자 확인 후 KMS 암호화 적용
    """
    if not not_kms_encrypted_trails: return

    cloudtrail = boto3.client('cloudtrail')
    kms = boto3.client('kms')
    print("[FIX] 4.5 CloudTrail SSE-KMS 암호화 조치를 시작합니다.")

    try:
        # 사용할 KMS 키 선택 (기본 aws/cloudtrail 키 또는 사용자 지정 키)
        key_arn = input("  -> 사용할 KMS Key ARN을 입력하세요 (기본값을 사용하려면 Enter): ").strip()
        if not key_arn:
            # 기본 별칭(alias)으로 키 ARN 조회
            aliases = kms.list_aliases()['Aliases']
            default_key = next((a['TargetKeyId'] for a in aliases if a['AliasName'] == 'alias/aws/cloudtrail'), None)
            if not default_key:
                print("     [ERROR] 기본 CloudTrail KMS 키(alias/aws/cloudtrail)를 찾을 수 없습니다. 수동으로 생성하거나 ARN을 입력하세요.")
                return
            account_id = boto3.client('sts').get_caller_identity()['Account']
            region = boto3.session.Session().region_name
            key_arn = f"arn:aws:kms:{region}:{account_id}:key/{default_key}"
            print(f"     [INFO] 기본 KMS 키 '{key_arn}'을(를) 사용합니다.")

        for trail_name in not_kms_encrypted_trails:
            if input(f"  -> Trail '{trail_name}'에 KMS 암호화를 적용하시겠습니까? (y/n): ").lower() == 'y':
                try:
                    cloudtrail.update_trail(Name=trail_name, KmsKeyId=key_arn)
                    print(f"     [SUCCESS] Trail '{trail_name}'에 KMS 암호화를 적용했습니다.")
                except ClientError as e:
                    print(f"     [ERROR] Trail '{trail_name}' 암호화 적용 실패: {e}")

    except ClientError as e:
        print(f"     [ERROR] KMS 키 정보 조회 중 오류 발생: {e}")

if __name__ == "__main__":
    trails = check()
    fix(trails)