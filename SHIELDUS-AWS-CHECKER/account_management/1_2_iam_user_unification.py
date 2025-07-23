import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timezone


def check():
    """
    [1.2] IAM 사용자 계정 단일화 관리
    - 참고: 콘솔 로그인 및 Access Key 사용 이력을 기준으로
            90일 이상 미사용된 IAM 사용자를 안내합니다.
    - 단, 1명의 담당자가 다수의 계정을 사용하는지 여부는 수동 점검 필요
    """
    print("[INFO] 1.2 IAM 사용자 계정 단일화 관리 체크 중...")
    print("[ⓘ MANUAL] 1명의 담당자가 여러 개의 IAM 계정을 사용하는지에 대해서는 수동 점검이 필요합니다.")

    iam = boto3.client('iam')
    inactive_user_details = {}
    now = datetime.now(timezone.utc)

    try:
        paginator = iam.get_paginator('list_users')
        for page in paginator.paginate():
            for user in page['Users']:
                user_name = user['UserName']
                is_inactive = True

                # 콘솔 로그인 사용 이력 확인
                last_password_use = user.get('PasswordLastUsed')
                if last_password_use and (now - last_password_use).days <= 90:
                    is_inactive = False

                # Access Key 사용 이력 또는 생성일 확인
                if is_inactive:
                    keys_response = iam.list_access_keys(UserName=user_name)
                    has_active_key = False

                    for key in keys_response['AccessKeyMetadata']:
                        if key['Status'] == 'Active':
                            has_active_key = True
                            last_used_info = iam.get_access_key_last_used(AccessKeyId=key['AccessKeyId'])
                            last_used_date = last_used_info.get('AccessKeyLastUsed', {}).get('LastUsedDate')
                            create_date = key['CreateDate']

                            if last_used_date:
                                if (now - last_used_date).days <= 90:
                                    is_inactive = False
                                    break
                            else:
                                # 사용 이력은 없지만 생성된 지 90일 미만이면 활성으로 간주
                                if (now - create_date).days <= 90:
                                    is_inactive = False
                                    break

                    # 판단 결과에 따라 사용자 분류
                    if has_active_key and is_inactive:
                        inactive_user_details[user_name] = "액세스 키 90일 이상 미사용"
                    elif not has_active_key and not last_password_use:
                        inactive_user_details[user_name] = "활동 기록 없음"
                    elif is_inactive and last_password_use:
                        inactive_user_details[user_name] = f"콘솔 비활성: {(now - last_password_use).days}일"

        # 결과 출력
        if not inactive_user_details:
            print("[참고] 1.2 장기 미사용 또는 불필요한 사용자 계정이 발견되지 않았습니다.")
        else:
            print(f"[참고] 1.2 미사용 사용자 계정이 존재합니다 ({len(inactive_user_details)}개).")
            for user, reason in inactive_user_details.items():
                print(f"  ├─ 비활성 의심 사용자: {user} ({reason})")

        return True

    except ClientError as e:
        print(f"[ERROR] IAM 사용자 활동 정보를 가져오는 중 오류 발생: {e}")
        return False


if __name__ == "__main__":
    check()
