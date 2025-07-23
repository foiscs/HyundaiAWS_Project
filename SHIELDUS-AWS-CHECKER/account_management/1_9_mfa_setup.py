import boto3
from botocore.exceptions import ClientError

def check():
    """
    [1.9] MFA 설정
    - Root 계정 및 콘솔 사용자에 대해 MFA 활성화 여부를 점검하고 미설정 사용자 목록을 반환
    """
    print("[INFO] 1.9 MFA 설정 체크 중...")
    iam = boto3.client('iam')
    findings = {'root_mfa_disabled': False, 'users_without_mfa': []}
    
    try:
        if iam.get_account_summary()['SummaryMap']['AccountMFAEnabled'] == 0:
            findings['root_mfa_disabled'] = True
            print("[⚠ WARNING] 1.9 Root 계정에 MFA가 활성화되어 있지 않습니다.")
        else:
            print("[✓ COMPLIANT] 1.9 Root 계정에 MFA가 활성화되어 있습니다.")
    except ClientError as e:
        print(f"[ERROR] 계정 요약 정보를 가져오는 중 오류 발생: {e}")

    try:
        for user in iam.list_users()['Users']:
            user_name = user['UserName']
            try:
                iam.get_login_profile(UserName=user_name)  # 해당 사용자에게 콘솔 로그인 권한이 있는지 확인 (없으면 예외 발생)
                if not iam.list_mfa_devices(UserName=user_name).get('MFADevices'):
                    findings['users_without_mfa'].append(user_name)
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchEntity': continue
                else: raise e
        
        if not findings['users_without_mfa']:
            print("[✓ COMPLIANT] 1.9 모든 콘솔 접근 가능 IAM 사용자에게 MFA가 활성화되어 있습니다.")
        else:
            print(f"[⚠ WARNING] 1.9 MFA가 비활성화된 콘솔 접근 사용자 존재 ({len(findings['users_without_mfa'])}명)")
            print(f"  ├─ MFA 비활성 사용자: {', '.join(findings['users_without_mfa'])}")
            
        return findings
    except ClientError as e:
        print(f"[ERROR] IAM 사용자 MFA 정보를 가져오는 중 오류 발생: {e}")
        return findings

def fix(findings):
    """
    [1.9] MFA 설정 조치
    - MFA 설정은 사용자의 물리적 디바이스가 필요하므로 자동 조치가 불가능함. 수동 조치 안내
    """
    if not findings['root_mfa_disabled'] and not findings['users_without_mfa']:
        return

    print("[FIX] 1.9 MFA 설정은 사용자의 물리적/가상 디바이스 등록이 필요하므로 자동화할 수 없습니다.")
    if findings['root_mfa_disabled']:
        print("  └─ [Root 계정] AWS Management Console에 Root로 로그인하여 [내 보안 자격 증명]에서 MFA 디바이스를 할당하세요.")
    if findings['users_without_mfa']:
        print(f"  └─ [IAM 사용자] 다음 사용자들에게 각자 로그인하여 [내 보안 자격 증명]에서 MFA를 설정하도록 안내하세요: {', '.join(findings['users_without_mfa'])}")

if __name__ == "__main__":
    findings_dict = check()
    fix(findings_dict)