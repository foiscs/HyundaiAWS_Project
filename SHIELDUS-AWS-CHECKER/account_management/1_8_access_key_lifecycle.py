import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timezone

def check():
    """
    [1.8] Access Key 활성화 및 사용주기 관리
    - 생성된 지 60일이 지난 활성 Access Key (old_keys)
    - 30일 이상 사용되지 않은 활성 Access Key (unused_keys)
    - 위 두 목록을 딕셔너리로 반환
    """
    print("[INFO] 1.8 Access Key 활성화 및 사용주기 관리 체크 중...")
    iam = boto3.client('iam')
    findings = {'old_keys': [], 'unused_keys': []}
    now = datetime.now(timezone.utc)

    try:
        for user in iam.list_users()['Users']:
            user_name = user['UserName']
            for key in iam.list_access_keys(UserName=user_name)['AccessKeyMetadata']:
                if key['Status'] == 'Active':
                    access_key_id = key['AccessKeyId']
                    create_date = key['CreateDate']
                    
                    if (now - create_date).days > 60:
                        findings['old_keys'].append({'user': user_name, 'key_id': access_key_id, 'days': (now - create_date).days})

                    last_used_info = iam.get_access_key_last_used(AccessKeyId=access_key_id)
                    last_used_date = last_used_info.get('AccessKeyLastUsed', {}).get('LastUsedDate')
                    if last_used_date and (now - last_used_date).days > 30:
                        findings['unused_keys'].append({'user': user_name, 'key_id': access_key_id, 'days': (now - last_used_date).days})
                    elif not last_used_date and (now - create_date).days > 30:
                        findings['unused_keys'].append({'user': user_name, 'key_id': access_key_id, 'days': (now - create_date).days, 'note': '사용기록 없음'})

        if not findings['old_keys'] and not findings['unused_keys']:
            print("[✓ COMPLIANT] 1.8 모든 활성 Access Key가 주기 관리 기준을 준수합니다.")
        if findings['old_keys']:
            print(f"[⚠ WARNING] 1.8 생성된 지 60일이 경과한 Access Key가 존재합니다 ({len(findings['old_keys'])}개).")
            for k in findings['old_keys']: print(f"  ├─ {k['user']}의 키 ({k['key_id']}, 생성 후 {k['days']}일)")
        if findings['unused_keys']:
            print(f"[⚠ WARNING] 1.8 30일 이상 사용되지 않은 Access Key가 존재합니다 ({len(findings['unused_keys'])}개).")
            for k in findings['unused_keys']: print(f"  ├─ {k['user']}의 키 ({k['key_id']}, 미사용 {k['days']}일)")
        
        return findings
    except ClientError as e:
        print(f"[ERROR] Access Key 정보를 가져오는 중 오류 발생: {e}")
        return {}

def fix(findings):
    """
    [1.8] Access Key 활성화 및 사용주기 관리 조치
    - 오래되거나 미사용 키에 대해 비활성화/삭제 조치
    """
    if not findings.get('old_keys') and not findings.get('unused_keys'):
        return

    iam = boto3.client('iam')
    keys_to_action = {f['key_id']: f['user'] for f in findings.get('unused_keys', [])} # 미사용 키 우선 조치

    print("[FIX] 1.8 오래되거나 미사용 중인 Access Key에 대한 조치를 시작합니다.")
    for key_id, user_name in keys_to_action.items():
        choice = input(f"  -> 사용자 '{user_name}'의 미사용 키 '{key_id}'를 조치하시겠습니까? ([d]eactivate, [D]ELETE, [i]gnore): ").lower()
        if choice == 'd':
            try:
                iam.update_access_key(UserName=user_name, AccessKeyId=key_id, Status='Inactive')
                print(f"     [SUCCESS] 키 '{key_id}'를 비활성화했습니다.")
            except ClientError as e:
                print(f"     [ERROR] 키 비활성화 실패: {e}")
        elif choice == 'D':
             confirm = input(f"     정말로 키 '{key_id}'를 영구적으로 삭제하시겠습니까? (yes/no): ").lower()
             if confirm == 'yes':
                try:
                    iam.delete_access_key(UserName=user_name, AccessKeyId=key_id)
                    print(f"     [SUCCESS] 키 '{key_id}'를 삭제했습니다.")
                except ClientError as e:
                    print(f"     [ERROR] 키 삭제 실패: {e}")
        else:
            print(f"     [INFO] 키 '{key_id}' 조치를 건너뜁니다.")
    
    if findings.get('old_keys'):
        print("[INFO] 생성 후 60일이 경과한 키는 주기적으로 교체(rotation)하는 것을 권장합니다. 이는 자동화할 수 없습니다.")

if __name__ == "__main__":
    findings_dict = check()
    fix(findings_dict)