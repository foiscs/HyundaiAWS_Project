import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timezone
import re

def is_test_user(user_name):
    return bool(re.match(r'^(test|tmp|guest|retired|퇴직|미사용)', user_name, re.IGNORECASE))

def check():
    print("[INFO] 사용자 계정 점검 시작")
    iam = boto3.client('iam')

    now = datetime.now(timezone.utc)
    admin_users = set()
    test_users = set()

    try:
        paginator = iam.get_paginator('list_users')
        for page in paginator.paginate():
            for user in page['Users']:
                name = user['UserName']
                is_admin = False

                if is_test_user(name):
                    test_users.add(name)

                user_policies = iam.list_attached_user_policies(UserName=name)['AttachedPolicies']
                if any(p['PolicyArn'].endswith('/AdministratorAccess') for p in user_policies):
                    is_admin = True

                if not is_admin:
                    groups = iam.list_groups_for_user(UserName=name)['Groups']
                    for g in groups:
                        group_policies = iam.list_attached_group_policies(GroupName=g['GroupName'])['AttachedPolicies']
                        if any(p['PolicyArn'].endswith('/AdministratorAccess') for p in group_policies):
                            is_admin = True
                            break

                if is_admin:
                    admin_users.add(name)

        print(f"\n[RESULT] IAM 관리자: {len(admin_users)}명")
        print("  └ ", ', '.join(admin_users) if admin_users else "없음")

        print(f"\n[RESULT] 테스트/임시 계정: {len(test_users)}개")
        print("  └ ", ', '.join(test_users) if test_users else "없음")

        return {
            "admin_users": list(admin_users),
            "test_users": list(test_users)
        }

    except ClientError as e:
        print(f"[ERROR] 오류 발생: {e}")
        return {
            "admin_users": [],
            "test_users": []
        }

def fix(data):
    iam = boto3.client('iam')
    print("\n[FIX] 사용자 조치 안내")

    for user in data['admin_users']:
        confirm = input(f"→ '{user}'의 관리자 권한 제거할까요? (y/n): ").lower()
        if confirm == 'y':
            try:
                iam.detach_user_policy(UserName=user, PolicyArn='arn:aws:iam::aws:policy/AdministratorAccess')
                print(f"  ✔ 관리자 권한 제거 완료: {user}")
            except ClientError as e:
                print(f"  ✖ 실패: {e}")

    for user in data['test_users']:
        confirm = input(f"→ '{user}' 테스트 계정의 콘솔 로그인을 비활성화할까요? (y/n): ").lower()
        if confirm == 'y':
            try:
                iam.delete_login_profile(UserName=user)
                print(f"  ✔ 콘솔 로그인 제거 완료: {user}")
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchEntity':
                    print(f"  ℹ 이미 비활성화됨: {user}")
                else:
                    print(f"  ✖ 실패: {e}")

if __name__ == "__main__":
    results = check()
    fix(results)
