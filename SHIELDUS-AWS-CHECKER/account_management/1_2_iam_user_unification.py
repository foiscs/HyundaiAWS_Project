import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timezone

def check():
    """
    [1.2] IAM 사용자 계정 단일화 관리
    - 90일 이상 사용되지 않은 IAM 사용자를 점검하고, 해당 사용자 목록을 반환
    """
    print("[INFO] 1.2 IAM 사용자 계정 단일화 관리 체크 중...")
    iam = boto3.client('iam')
    inactive_user_details = {}
    now = datetime.now(timezone.utc)

    try:
        paginator = iam.get_paginator('list_users')
        for page in paginator.paginate():
            for user in page['Users']:
                user_name = user['UserName']
                is_inactive = True
                
                # 콘솔 마지막 사용 확인
                last_password_use = user.get('PasswordLastUsed')
                if last_password_use and (now - last_password_use).days <= 90:
                    is_inactive = False

                # Access Key 마지막 사용 확인
                if is_inactive:
                    keys_response = iam.list_access_keys(UserName=user_name)
                    has_active_key = False
                    for key in keys_response['AccessKeyMetadata']:
                        if key['Status'] == 'Active':
                            has_active_key = True
                            last_used_info = iam.get_access_key_last_used(AccessKeyId=key['AccessKeyId'])
                            last_used_date = last_used_info.get('AccessKeyLastUsed', {}).get('LastUsedDate')
                            if last_used_date and (now - last_used_date).days <= 90:
                                is_inactive = False
                                break
                    # 활성 키가 아예 없거나, 있어도 모두 90일 이상 미사용인 경우
                    if has_active_key and is_inactive:
                        inactive_user_details[user_name] = "액세스 키 90일 이상 미사용"
                    elif not has_active_key and not last_password_use:
                        inactive_user_details[user_name] = "활동 기록 없음"
                    elif is_inactive and last_password_use:
                         inactive_user_details[user_name] = f"콘솔 비활성: {(now - last_password_use).days}일"


        if not inactive_user_details:
            print("[✓ COMPLIANT] 1.2 장기 미사용 또는 불필요한 사용자 계정이 발견되지 않았습니다.")
        else:
            print(f"[⚠ WARNING] 1.2 장기 미사용(90일 이상) 사용자 계정이 존재합니다 ({len(inactive_user_details)}개).")
            for user, reason in inactive_user_details.items():
                print(f"  ├─ 비활성 의심 사용자: {user} ({reason})")
        
        return list(inactive_user_details.keys())

    except ClientError as e:
        print(f"[ERROR] IAM 사용자 활동 정보를 가져오는 중 오류 발생: {e}")
        return []

def fix(inactive_users):
    """
    [1.2] IAM 사용자 계정 단일화 관리 조치
    - 비활성 사용자에 대해 콘솔 로그인 비활성화 또는 사용자 삭제를 선택적으로 수행
    """
    if not inactive_users:
        return

    iam = boto3.client('iam')
    print("[FIX] 1.2 비활성 사용자에 대한 조치를 시작합니다.")
    for user_name in inactive_users:
        choice = input(f"  -> 사용자 '{user_name}'에 대한 조치를 선택하세요 ([d]eactivate login, [D]ELETE user, [i]gnore): ").lower()
        if choice == 'd':
            try:
                iam.delete_login_profile(UserName=user_name)
                print(f"     [SUCCESS] 사용자 '{user_name}'의 콘솔 로그인을 비활성화했습니다.")
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchEntity':
                    print(f"     [INFO] 사용자 '{user_name}'은(는) 이미 콘솔 로그인이 비활성화되어 있습니다.")
                else:
                    print(f"     [ERROR] 사용자 '{user_name}'의 콘솔 로그인 비활성화 실패: {e}")
        elif choice == 'D':
            confirm = input(f"     정말로 사용자 '{user_name}'을(를) 영구적으로 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다. (yes/no): ").lower()
            if confirm == 'yes':
                try:
                    # 순서: 로그인 프로필 -> Access Key -> 정책 -> 사용자
                    try: iam.delete_login_profile(UserName=user_name)
                    except ClientError: pass
                    for key in iam.list_access_keys(UserName=user_name)['AccessKeyMetadata']:
                        iam.delete_access_key(UserName=user_name, AccessKeyId=key['AccessKeyId'])
                    for policy in iam.list_attached_user_policies(UserName=user_name)['AttachedPolicies']:
                        iam.detach_user_policy(UserName=user_name, PolicyArn=policy['PolicyArn'])
                    iam.delete_user(UserName=user_name)
                    print(f"     [SUCCESS] 사용자 '{user_name}'을(를) 성공적으로 삭제했습니다.")
                except ClientError as e:
                    print(f"     [ERROR] 사용자 '{user_name}' 삭제 실패: {e}")
        else:
            print(f"     [INFO] 사용자 '{user_name}'에 대한 조치를 건너뜁니다.")

if __name__ == "__main__":
    inactive_user_list = check()
    fix(inactive_user_list)