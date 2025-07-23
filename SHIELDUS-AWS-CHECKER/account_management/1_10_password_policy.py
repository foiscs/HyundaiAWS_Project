import boto3
from botocore.exceptions import ClientError

def check():
    """
    [1.10] AWS 계정 패스워드 정책 관리
    - 계정의 패스워드 정책이 권장 기준을 충족하는지 점검하고, 미흡한 경우 True를 반환
    """
    print("[INFO] 1.10 AWS 계정 패스워드 정책 관리 체크 중...")
    print("[ⓘ INFO] Admin Console의 패스워드 복잡성 정책은 AWS 내부 정책에 의해 관리되며, IAM 정책만 점검할 수 있습니다.")
    iam = boto3.client('iam')
    is_non_compliant = False

    try:
        policy = iam.get_account_password_policy()['PasswordPolicy']
        findings = []
        
        if policy.get('MinimumPasswordLength', 0) < 8: findings.append("최소 길이 8 미만")
        
        complexity = sum([1 for k in ['RequireSymbols','RequireNumbers','RequireUppercaseCharacters','RequireLowercaseCharacters'] if policy.get(k)])
        if complexity < 3: findings.append("복잡도 3종류 미만")
        
        if not policy.get('PasswordReusePrevention'): findings.append("재사용 방지 미설정")
        
        if not policy.get('ExpirePasswords') or policy.get('MaxPasswordAge', 1000) > 90:
            findings.append("만료 기간 90일 초과 또는 미설정")

        if findings:
            is_non_compliant = True
            print("[⚠ WARNING] 1.10 패스워드 정책이 권장 기준을 충족하지 않습니다.")
            print(f"  └─ 미흡 항목: {', '.join(findings)}")
        else:
            print("[✓ COMPLIANT] 1.10 패스워드 정책이 권장 기준을 충족합니다.")
            
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            is_non_compliant = True
            print("[⚠ WARNING] 1.10 계정에 패스워드 정책이 설정되어 있지 않습니다.")
        else:
            print(f"[ERROR] 패스워드 정책 정보를 가져오는 중 오류 발생: {e}")

    return is_non_compliant

def fix(is_non_compliant):
    """
    [1.10] AWS 계정 패스워드 정책 관리 조치
    - 권장 기준으로 패스워드 정책을 업데이트
    """
    if not is_non_compliant:
        return

    iam = boto3.client('iam')
    choice = input("[FIX] 1.10 권장 기준에 따라 IAM 계정 암호 정책을 업데이트하시겠습니까? (y/n): ").lower()
    if choice == 'y':
        try:
            iam.update_account_password_policy(
                MinimumPasswordLength=8,
                RequireSymbols=True,
                RequireNumbers=True,
                RequireUppercaseCharacters=True,
                RequireLowercaseCharacters=True,
                AllowUsersToChangePassword=True,
                MaxPasswordAge=90,
                PasswordReusePrevention=5,
                HardExpiry=False
            )
            print("     [SUCCESS] 계정 암호 정책을 성공적으로 업데이트했습니다.")
        except ClientError as e:
            print(f"     [ERROR] 암호 정책 업데이트 실패: {e}")
    else:
        print("     [INFO] 암호 정책 업데이트를 건너뜁니다.")

if __name__ == "__main__":
    non_compliant = check()
    fix(non_compliant)