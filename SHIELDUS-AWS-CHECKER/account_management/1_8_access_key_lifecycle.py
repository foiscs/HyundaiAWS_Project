import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timezone

def check():
    """
    [1.8] Access Key 활성화 및 사용주기 관리
    - 루트 계정 Access Key 존재 여부 확인
    - IAM 사용자 키 생성일/사용일 점검 (60일 초과 생성, 30일 이상 미사용)
    """
    print("[INFO] 1.8 Access Key 활성화 및 사용주기 관리 체크 중...")
    iam = boto3.client('iam')
    findings = {
        'root_key_exists': False,
        'old_keys': [],
        'unused_keys': []
    }
    now = datetime.now(timezone.utc)

    try:
        # ✅ 루트 계정 Access Key 존재 여부 확인
        summary = iam.get_account_summary()
        if summary['SummaryMap'].get('AccountAccessKeysPresent', 0) > 0:
            findings['root_key_exists'] = True
            print("[⚠ WARNING] 루트 계정에 Access Key가 존재합니다. 즉시 삭제 권장.")
        else:
            print("[✓ COMPLIANT] 루트 계정에 Access Key가 존재하지 않습니다.")

        # ✅ IAM 사용자 키 점검
        for user in iam.list_users()['Users']:
            user_name = user['UserName']
            for key in iam.list_access_keys(UserName=user_name)['AccessKeyMetadata']:
                if key['Status'] == 'Active':
                    access_key_id = key['AccessKeyId']
                    create_date = key['CreateDate']
                    
                    # 생성 후 60일 초과
                    if (now - create_date).days > 60:
                        findings['old_keys'].append({
                            'user': user_name,
                            'key_id': access_key_id,
                            'days': (now - create_date).days
                        })

                    # 마지막 사용 정보 조회
                    last_used_info = iam.get_access_key_last_used(AccessKeyId=access_key_id)
                    last_used_date = last_used_info.get('AccessKeyLastUsed', {}).get('LastUsedDate')
                    
                    # 30일 초과 미사용 or 사용 이력 없음
                    if last_used_date and (now - last_used_date).days > 30:
                        findings['unused_keys'].append({
                            'user': user_name,
                            'key_id': access_key_id,
                            'days': (now - last_used_date).days
                        })
                    elif not last_used_date and (now - create_date).days > 30:
                        findings['unused_keys'].append({
                            'user': user_name,
                            'key_id': access_key_id,
                            'days': (now - create_date).days,
                            'note': '사용기록 없음'
                        })

        # ✅ 출력 정리
        if findings['old_keys']:
            print(f"[⚠ WARNING] 생성 후 60일이 경과한 Access Key 존재: {len(findings['old_keys'])}개")
            for k in findings['old_keys']:
                print(f"  ├─ {k['user']}의 키 ({k['key_id']}, 생성 {k['days']}일 경과)")

        if findings['unused_keys']:
            print(f"[⚠ WARNING] 30일 이상 사용되지 않은 Access Key 존재: {len(findings['unused_keys'])}개")
            for k in findings['unused_keys']:
                note = f" ({k.get('note')})" if 'note' in k else ""
                print(f"  ├─ {k['user']}의 키 ({k['key_id']}, 미사용 {k['days']}일{note})")

        if not findings['old_keys'] and not findings['unused_keys']:
            print("[✓ COMPLIANT] 모든 IAM 사용자 Access Key가 보안 기준을 충족합니다.")

        return findings

    except ClientError as e:
        print(f"[ERROR] 점검 중 오류 발생: {e}")
        return findings

def fix(findings):
    """
    [1.8] Access Key 활성화 및 사용주기 관리 조치
    - 미사용 키에 대해 비활성화 또는 삭제 안내
    """
    iam = boto3.client('iam')

    # ✅ 루트 키 조치 안내
    if findings.get('root_key_exists'):
        print("\n[FIX] 루트 계정에 Access Key가 존재합니다. 즉시 삭제하세요.")
        print("  └─ AWS 콘솔 > '내 보안 자격 증명' > 'Access Key'에서 삭제 가능합니다.")

    # ✅ 미사용 키 조치
    keys_to_action = {f['key_id']: f['user'] for f in findings.get('unused_keys', [])}
    if keys_to_action:
        print("\n[FIX] 미사용 Access Key 조치를 시작합니다.")
        for key_id, user_name in keys_to_action.items():
            choice = input(f"→ 사용자 '{user_name}'의 키 '{key_id}'를 조치하시겠습니까? ([d]eactivate, [D]ELETE, [i]gnore): ").lower()
            if choice == 'd':
                try:
                    iam.update_access_key(UserName=user_name, AccessKeyId=key_id, Status='Inactive')
                    print(f"   ✔ 비활성화 완료: {key_id}")
                except ClientError as e:
                    print(f"   ✖ 실패: {e}")
            elif choice == 'D':
                confirm = input(f"   정말 삭제하시겠습니까? (yes/no): ").lower()
                if confirm == 'yes':
                    try:
                        iam.delete_access_key(UserName=user_name, AccessKeyId=key_id)
                        print(f"   ✔ 삭제 완료: {key_id}")
                    except ClientError as e:
                        print(f"   ✖ 삭제 실패: {e}")
            else:
                print(f"   ⏭ 키 '{key_id}'는 조치하지 않음")

    # ✅ 오래된 키 교체 안내
    if findings.get('old_keys'):
        print("\n[INFO] 생성된 지 60일 이상 경과한 키는 주기적으로 교체(rotation)해야 합니다.")
        print("  └─ 자동화는 권장되지 않으며, 수동으로 새 키를 생성한 뒤 기존 키를 삭제하세요.")

if __name__ == "__main__":
    results = check()
    fix(results)