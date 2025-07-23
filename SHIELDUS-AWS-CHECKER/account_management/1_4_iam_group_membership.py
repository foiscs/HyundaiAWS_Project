import boto3
from botocore.exceptions import ClientError


def check():
    """
    [1.4] IAM 그룹 사용자 계정 관리
    - 모든 IAM 사용자가 하나 이상의 그룹에 속해 있는지 점검하고, 미소속 사용자 목록을 반환
    """
    print("[INFO] 1.4 IAM 그룹 사용자 계정 관리 체크 중...")
    iam = boto3.client('iam')
    users_not_in_group = []

    try:
        paginator = iam.get_paginator('list_users')
        for page in paginator.paginate():
            for user in page['Users']:
                user_name = user['UserName']
                groups_response = iam.list_groups_for_user(UserName=user_name)
                if not groups_response.get('Groups'):
                    users_not_in_group.append(user_name)
        
        if not users_not_in_group:
            print("[✓ COMPLIANT] 1.4 모든 사용자가 그룹에 속해 있습니다.")
        else:
            print(f"[⚠ WARNING] 1.4 그룹에 속하지 않은 사용자 존재 ({len(users_not_in_group)}명)")
            print(f"  ├─ 그룹 미소속 사용자: {', '.join(users_not_in_group)}")
        
        return users_not_in_group
    
    except ClientError as e:
        print(f"[ERROR] IAM 사용자 그룹 정보를 가져오는 중 오류 발생: {e}")
        return []


def fix(users_not_in_group):
    """
    [1.4] IAM 그룹 사용자 계정 관리 조치
    - 그룹에 속하지 않은 사용자를 대화형으로 특정 그룹에 추가
    - 그룹이 없을 경우 새 그룹을 생성할 수 있음
    """
    if not users_not_in_group:
        return

    iam = boto3.client('iam')
    print("[FIX] 1.4 그룹에 속하지 않은 사용자에 대한 조치를 시작합니다.")

    try:
        # 현재 그룹 목록 조회
        group_list_response = iam.list_groups()
        available_groups = [group['GroupName'] for group in group_list_response['Groups']]

        # 그룹이 하나도 없는 경우
        if not available_groups:
            print("  └─ [INFO] 현재 IAM 그룹이 없습니다.")
            create_choice = input("  -> 새 그룹을 생성하시겠습니까? (y/n): ").lower()
            if create_choice == 'y':
                group_name = input("     생성할 그룹 이름을 입력하세요: ")
                try:
                    iam.create_group(GroupName=group_name)
                    print(f"     [SUCCESS] 그룹 '{group_name}' 생성 완료.")
                    available_groups.append(group_name)
                except ClientError as e:
                    print(f"     [ERROR] 그룹 생성 실패: {e}")
                    return
            else:
                print("  └─ [INFO] 그룹이 없으므로 조치를 중단합니다.")
                return

        print(f"  -> 사용 가능한 그룹: {', '.join(available_groups)}")

        for user_name in users_not_in_group:
            choice = input(f"  -> 사용자 '{user_name}'을(를) 그룹에 추가하시겠습니까? (y/n): ").lower()
            if choice == 'y':
                group_name = input(f"     '{user_name}'을(를) 추가할 그룹 이름을 입력하세요: ")
                if group_name in available_groups:
                    try:
                        iam.add_user_to_group(UserName=user_name, GroupName=group_name)
                        print(f"     [SUCCESS] 사용자 '{user_name}'을(를) 그룹 '{group_name}'에 추가했습니다.")
                    except ClientError as e:
                        print(f"     [ERROR] 그룹 추가 실패: {e}")
                else:
                    print(f"     [ERROR] 그룹 '{group_name}'이(가) 존재하지 않습니다.")
            else:
                print(f"     [INFO] 사용자 '{user_name}'의 그룹 추가를 건너뜁니다.")

    except ClientError as e:
        print(f"[ERROR] 그룹 정보 조회 중 오류 발생: {e}")


if __name__ == "__main__":
    user_list = check()
    fix(user_list)
