import boto3
from botocore.exceptions import ClientError

def check():
    """
    [1.3] IAM 사용자 계정 식별 관리
    - 모든 IAM 사용자가 식별을 위한 태그를 가지고 있는지 점검하고, 태그 없는 사용자 목록을 반환
    """
    print("[INFO] 1.3 IAM 사용자 계정 식별 관리 체크 중...")
    iam = boto3.client('iam')
    untagged_users = []

    try:
        paginator = iam.get_paginator('list_users')
        for page in paginator.paginate():
            for user in page['Users']:
                user_name = user['UserName']
                tags_response = iam.list_user_tags(UserName=user_name)
                if not tags_response.get('Tags'):
                    untagged_users.append(user_name)

        if not untagged_users:
            print("[✓ COMPLIANT] 1.3 모든 사용자 계정에 태그가 존재합니다.")
        else:
            print(f"[⚠ WARNING] 1.3 태그가 없는 사용자 계정 존재 ({len(untagged_users)}개)")
            print(f"  ├─ 태그 없는 사용자: {', '.join(untagged_users)}")
        
        return untagged_users

    except ClientError as e:
        print(f"[ERROR] IAM 사용자 태그 정보를 가져오는 중 오류 발생: {e}")
        return []

def fix(untagged_users):
    """
    [1.3] IAM 사용자 계정 식별 관리 조치
    - 태그가 없는 사용자에게 대화형으로 태그를 추가
    """
    if not untagged_users:
        return

    iam = boto3.client('iam')
    print("[FIX] 1.3 태그가 없는 사용자에 대한 조치를 시작합니다.")
    for user_name in untagged_users:
        choice = input(f"  -> 사용자 '{user_name}'에 태그를 추가하시겠습니까? (y/n): ").lower()
        if choice == 'y':
            tags = []
            while True:
                key = input("     태그 키를 입력하세요 (완료하려면 Enter): ")
                if not key:
                    break
                value = input(f"     '{key}'의 값(Value)을 입력하세요: ")
                tags.append({'Key': key, 'Value': value})
            
            if tags:
                try:
                    iam.tag_user(UserName=user_name, Tags=tags)
                    print(f"     [SUCCESS] 사용자 '{user_name}'에 {len(tags)}개의 태그를 추가했습니다.")
                except ClientError as e:
                    print(f"     [ERROR] 태그 추가 실패: {e}")
        else:
            print(f"     [INFO] 사용자 '{user_name}'의 태그 추가를 건너뜁니다.")

if __name__ == "__main__":
    untagged_user_list = check()
    fix(untagged_user_list)