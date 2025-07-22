import boto3
from botocore.exceptions import ClientError

def check():
    """
    [1.1] 사용자 계정 관리
    - AdministratorAccess 권한을 가진 IAM 사용자가 최소한으로 유지되는지 점검하고, 해당 사용자 목록을 반환
    """
    print("[INFO] 1.1 사용자 계정 관리 체크 중...")
    iam = boto3.client('iam')
    policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
    admin_users = []
    
    try:
        paginator = iam.get_paginator('list_entities_for_policy')
        for page in paginator.paginate(PolicyArn=policy_arn, EntityFilter='User'):
            admin_users.extend([user['UserName'] for user in page.get('PolicyUsers', [])])

        if not admin_users:
            print("[✓ COMPLIANT] 1.1 관리자 권한(AdministratorAccess)을 가진 사용자가 없습니다.")
        elif len(admin_users) < 3:
            print(f"[✓ COMPLIANT] 1.1 관리자 권한 사용자 수가 적절함 ({len(admin_users)}명)")
            print(f"  └─ 관리자: {', '.join(admin_users)}")
        else:
            print(f"[⚠ WARNING] 1.1 관리자 권한(AdministratorAccess)을 가진 사용자가 많습니다. ({len(admin_users)}명)")
            print(f"  ├─ 관리자 목록: {', '.join(admin_users)}")
            print("  └─ 🔧 불필요한 관리자 계정의 권한을 축소하세요.")
        
        return admin_users # 조치를 위해 관리자 목록 반환

    except ClientError as e:
        print(f"[ERROR] 사용자 계정 정보를 가져오는 중 오류 발생: {e}")
        return []

def fix(admin_users):
    """
    [1.1] 사용자 계정 관리 조치
    - 관리자 권한 축소는 매우 민감한 작업이므로 자동 조치 대신 수동 조치 방법을 안내
    """
    if not admin_users:
        return

    print("[FIX] 1.1 관리자 권한 사용자 조치는 매우 중요하고 위험하므로 자동화되지 않습니다.")
    print("  └─ 각 관리자 계정의 필요성을 검토하고, 불필요한 경우 아래 명령어를 사용하여 직접 권한을 축소해야 합니다.")
    for user in admin_users:
        print(f"     aws iam detach-user-policy --user-name {user} --policy-arn arn:aws:iam::aws:policy/AdministratorAccess")

if __name__ == "__main__":
    admin_user_list = check()
    fix(admin_user_list)