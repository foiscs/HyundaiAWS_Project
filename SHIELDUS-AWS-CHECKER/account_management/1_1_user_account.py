import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timezone
import re

def is_test_user(user_name):
    return bool(re.match(r'^(test|tmp|guest|retired|퇴직|미사용)', user_name, re.IGNORECASE))

def check():
    print("[INFO] 사용자 계정 점검 시작")
    now = datetime.now(timezone.utc)
    threshold_days = 180

    iam = boto3.client('iam')
    admin_users = set()
    test_users = set()
    long_unused_keys = {}
    sso_admins = []

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

                key_data = iam.list_access_keys(UserName=name)['AccessKeyMetadata']
                for key in key_data:
                    if key['Status'] == 'Active':
                        key_id = key['AccessKeyId']
                        created = key['CreateDate']
                        last_used_info = iam.get_access_key_last_used(AccessKeyId=key_id)
                        last_used = last_used_info.get('AccessKeyLastUsed', {}).get('LastUsedDate')

                        if last_used:
                            days_unused = (now - last_used).days
                            if days_unused > threshold_days:
                                long_unused_keys[name] = (key_id, f"{days_unused}일")
                        else:
                            days_created = (now - created).days
                            if days_created > threshold_days:
                                long_unused_keys[name] = (key_id, f"Never Used, Created {days_created}일 전")

        # SSO 사용자 관리자 권한 탐지
        try:
            sso_admin = boto3.client('sso-admin')
            identitystore = boto3.client('identitystore')
            instances = sso_admin.list_instances()['Instances']
            if instances:
                instance_arn = instances[0]['InstanceArn']
                identity_store_id = instances[0]['IdentityStoreId']
                permission_sets = sso_admin.list_permission_sets(InstanceArn=instance_arn)['PermissionSets']

                for ps_arn in permission_sets:
                    policy = sso_admin.describe_permission_set(InstanceArn=instance_arn, PermissionSetArn=ps_arn)
                    name = policy['PermissionSet']['Name']
                    if 'admin' in name.lower():
                        assignments = sso_admin.list_account_assignments(
                            InstanceArn=instance_arn,
                            PermissionSetArn=ps_arn,
                            MaxResults=100
                        )
                        for a in assignments['AccountAssignments']:
                            principal_id = a['PrincipalId']
                            principal_type = a['PrincipalType']
                            if principal_type == 'USER':
                                user_detail = identitystore.describe_user(IdentityStoreId=identity_store_id, UserId=principal_id)
                                sso_admins.append(user_detail['UserName'])

        except ClientError:
            print("[WARN] SSO 사용자 또는 권한 확인 실패 (권한 부족 또는 미구성)")

        print(f"\n[RESULT] IAM 관리자: {len(admin_users)}명")
        print("  └ ", ', '.join(admin_users) if admin_users else "없음")

        print(f"\n[RESULT] Access Key 장기 미사용 사용자: {len(long_unused_keys)}명")
        for user, (key_id, days) in long_unused_keys.items():
            print(f"  ├─ {user} (Key: {key_id}, 미사용: {days})")

        print(f"\n[RESULT] 테스트/임시 계정: {len(test_users)}개")
        print("  └ ", ', '.join(test_users) if test_users else "없음")

        print(f"\n[RESULT] SSO 관리자: {len(sso_admins)}명")
        print("  └ ", ', '.join(sso_admins) if sso_admins else "없음")

        return {
            "admin_users": list(admin_users),
            "long_unused_keys": long_unused_keys,
            "test_users": list(test_users),
            "sso_admins": sso_admins
        }

    except ClientError as e:
        print(f"[ERROR] 오류 발생: {e}")
        return {
            "admin_users": [],
            "long_unused_keys": {},
            "test_users": [],
            "sso_admins": []
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

    for user, (key_id, _) in data['long_unused_keys'].items():
        confirm = input(f"→ '{user}'의 Access Key {key_id} 비활성화할까요? (y/n): ").lower()
        if confirm == 'y':
            try:
                iam.update_access_key(UserName=user, AccessKeyId=key_id, Status='Inactive')
                print(f"  ✔ Access Key 비활성화 완료: {user}")
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

    if data['sso_admins']:
        print("\n[FIX] SSO 관리자 권한은 AWS 콘솔(Single Sign-On → Permission Sets)에서 수동으로 제거해야 합니다.")
        print("  - 자동화 API는 존재하지만, 실수 위험이 높아 수동 검토 권장.")

if __name__ == "__main__":
    results = check()
    fix(results)
