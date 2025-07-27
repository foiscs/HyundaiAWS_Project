import boto3
from botocore.exceptions import ClientError

def check():
    print("[INFO] 3.7 S3 버킷/객체 접근 관리 체크 중...")
    s3 = boto3.client('s3')
    s3_control = boto3.client('s3control')
    sts = boto3.client('sts')

    findings = {
        'account_block_off': False,
        'bucket_acl_issues': [],
        'object_acl_issues': []
    }

    try:
        account_id = sts.get_caller_identity()['Account']
        try:
            pab_config = s3_control.get_public_access_block(AccountId=account_id)['PublicAccessBlockConfiguration']
            all_blocked = all(pab_config.get(k, False) for k in [
                'BlockPublicAcls', 'IgnorePublicAcls', 'BlockPublicPolicy', 'RestrictPublicBuckets'
            ])

            if all_blocked:
                print("[✅ 안전] 계정 수준 퍼블릭 액세스 차단이 완전히 활성화되어 있습니다.")
                return {}
            findings['account_block_off'] = True
            print("[⚠ 위험] 계정 수준 퍼블릭 액세스 차단에서 일부 설정이 비활성화되어 있습니다.")
            for k, desc in {
                'IgnorePublicAcls': '퍼블릭 ACL 무시',
                'BlockPublicAcls': 'ACL을 통한 퍼블릭 액세스 차단',
                'BlockPublicPolicy': '퍼블릭 정책 거부',
                'RestrictPublicBuckets': '퍼블릭 정책 제한'
            }.items():
                if not pab_config.get(k, False):
                    print(f"    └─ {desc}")

        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchPublicAccessBlockConfiguration':
                findings['account_block_off'] = True
                print("[⚠ 위험] 퍼블릭 액세스 차단 설정이 없습니다.")
            else:
                print(f"[ERROR] 퍼블릭 액세스 차단 확인 실패: {e}")
                return {}

        if findings['account_block_off']:
            buckets = s3.list_buckets().get('Buckets', [])
            if not buckets:
                print("[INFO] S3 버킷 없음.")
                return findings

            print(f"[INFO] {len(buckets)}개 버킷 점검 중...")
            for b in buckets:
                name = b['Name']
                object_count = _count_objects(s3, name)
                print(f"  └─ {name} ({object_count}개 객체 확인)")
                findings['bucket_acl_issues'].extend(_check_bucket_acl(s3, name))
                findings['object_acl_issues'].extend(_check_object_acls(s3, name))

        _print_findings_summary(findings)
        return findings if any(findings.values()) else {}

    except ClientError as e:
        print(f"[ERROR] S3 점검 실패: {e}")
        return {}

def _count_objects(s3, bucket):
    paginator = s3.get_paginator('list_objects_v2')
    count = 0
    try:
        for page in paginator.paginate(Bucket=bucket):
            count += len(page.get('Contents', []))
    except:
        pass
    return count

def _check_bucket_acl(s3, bucket_name):
    issues = []
    try:
        acl = s3.get_bucket_acl(Bucket=bucket_name)
        for grant in acl.get('Grants', []):
            grantee = grant.get('Grantee', {})
            permission = grant.get('Permission')
            uri = grantee.get('URI', '')
            if grantee.get('Type') == 'Group':
                if 'AllUsers' in uri:
                    issues.append(_make_acl_issue('bucket_acl', bucket_name, None, 'AllUsers', permission, 'HIGH'))
                elif 'AuthenticatedUsers' in uri:
                    issues.append(_make_acl_issue('bucket_acl', bucket_name, None, 'AuthenticatedUsers', permission, 'MEDIUM'))
    except ClientError as e:
        print(f"    [WARNING] 버킷 '{bucket_name}' ACL 확인 실패: {e}")
    return issues

def _check_object_acls(s3, bucket_name):
    issues = []
    try:
        paginator = s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket_name):
            for obj in page.get('Contents', []):
                key = obj['Key']
                try:
                    acl = s3.get_object_acl(Bucket=bucket_name, Key=key)
                    for grant in acl.get('Grants', []):
                        grantee = grant.get('Grantee', {})
                        permission = grant.get('Permission')
                        uri = grantee.get('URI', '')
                        if grantee.get('Type') == 'Group':
                            if 'AllUsers' in uri:
                                issues.append(_make_acl_issue('object_acl', bucket_name, key, 'AllUsers', permission, 'HIGH'))
                            elif 'AuthenticatedUsers' in uri:
                                issues.append(_make_acl_issue('object_acl', bucket_name, key, 'AuthenticatedUsers', permission, 'MEDIUM'))
                except ClientError as e:
                    if 'AccessDenied' not in str(e):
                        print(f"    [WARNING] 객체 '{key}' ACL 확인 실패: {e}")
    except ClientError as e:
        print(f"    [WARNING] 버킷 '{bucket_name}' 객체 목록 조회 실패: {e}")
    return issues

def _make_acl_issue(issue_type, bucket, obj, grantee_type, permission, risk):
    return {
        'type': issue_type,
        'bucket': bucket,
        'object': obj,
        'grantee_type': f"{grantee_type} (퍼블릭)",
        'permission': permission,
        'risk_level': risk
    }

def _print_findings_summary(findings):
    print("\n" + "="*60)
    print("📊 S3 보안 점검 결과 요약")
    print("="*60)

    if not any(findings.values()):
        print("[✅ 안전] 모든 S3 리소스가 보안 기준을 준수합니다.")
        return

    if findings.get('account_block_off'):
        print("[⚠ 중요] 계정 수준 퍼블릭 액세스 차단이 비활성화되어 있습니다.")

    def print_acl_issues(title, issues):
        print(f"\n[{title}] {len(issues)}건 발견:")
        for i, issue in enumerate(issues[:5]):
            icon = "🔴" if issue['risk_level'] == 'HIGH' else "🟡"
            resource = f"{issue['bucket']}/{issue['object']}" if issue['object'] else issue['bucket']
            print(f"  {icon} {resource}: {issue['grantee_type']}에게 {issue['permission']} 권한 부여")
        if len(issues) > 5:
            print(f"  └─ ... 외 {len(issues) - 5}건 더 있음")

    if findings['bucket_acl_issues']:
        print_acl_issues("🪣 버킷 ACL 문제", findings['bucket_acl_issues'])

    if findings['object_acl_issues']:
        print_acl_issues("📄 객체 ACL 문제", findings['object_acl_issues'])

def fix(findings):
    print("\n" + "="*60)
    print("🔧 S3 보안 조치 시작")
    print("="*60)

    # 1. 계정 전체 퍼블릭 차단
    account_blocked = False
    if findings.get('account_block_off'):
        account_blocked = _handle_account_block()

    # 계정 수준 차단이 완료되면 종료
    if account_blocked:
        return

    # 2. 퍼블릭 문제가 있는 버킷만 수집
    problem_buckets = set()
    
    # 버킷 ACL 문제가 있는 버킷들
    for issue in findings.get('bucket_acl_issues', []):
        print(f"\n[INFO] 버킷 '{issue['bucket']}'에 퍼블릭 ACL 문제가 있습니다.")
        problem_buckets.add(issue['bucket'])
    
    # 객체 ACL 문제가 있는 버킷들
    for issue in findings.get('object_acl_issues', []):
        problem_buckets.add(issue['bucket'])
    
    if problem_buckets:
        print(f"\n[INFO] 퍼블릭 접근 문제가 있는 {len(problem_buckets)}개 버킷에 대해 처리를 시작합니다.")
        for bucket in problem_buckets:
            _handle_bucket_remediation(bucket, findings)
    else:
        print("\n[INFO] 퍼블릭 접근 문제가 있는 버킷이 없습니다.")

def _handle_account_block():
    print("\n 계정 수준 퍼블릭 액세스 차단 설정")
    choice = input("  → 전체 차단 활성화(y/n): ").lower()
    if choice == 'y':
        try:
            s3_control = boto3.client('s3control')
            sts = boto3.client('sts')
            account_id = sts.get_caller_identity()['Account']
            s3_control.put_public_access_block(
                AccountId=account_id,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': True,
                    'IgnorePublicAcls': True,
                    'BlockPublicPolicy': True,
                    'RestrictPublicBuckets': True
                }
            )
            print("  ✅ 계정 전체 퍼블릭 차단 설정 완료")
            print("  💡 모든 S3 리소스에 퍼블릭 액세스 차단이 적용되었습니다.")
            return True
        except ClientError as e:
            print(f"  ❌ 차단 실패: {e}")
            return False
    return False

def _handle_bucket_remediation(bucket, findings):
    # 해당 버킷의 문제 수집
    bucket_acl_issues = [x for x in findings.get('bucket_acl_issues', []) if x['bucket'] == bucket]
    object_acl_issues = [x for x in findings.get('object_acl_issues', []) if x['bucket'] == bucket]
    
    total_issues = len(bucket_acl_issues) + len(object_acl_issues)
    
    # 2. 버킷별 퍼블릭 차단
    print(f"\n버킷 '{bucket}'에 {total_issues}개의 퍼블릭 접근 문제가 있습니다.")
    choice = input(f"버킷 '{bucket}' 퍼블릭 차단 활성화(y/n): ").lower()
    
    if choice == 'y':
        try:
            s3 = boto3.client('s3')
            s3.put_public_access_block(
                Bucket=bucket,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': True,
                    'IgnorePublicAcls': True,
                    'BlockPublicPolicy': True,
                    'RestrictPublicBuckets': True
                }
            )
            print(f"  ✅ 버킷 '{bucket}' 퍼블릭 차단 완료")
            return  # 다음 버킷으로
        except ClientError as e:
            print(f"  ❌ 버킷 '{bucket}' 차단 실패: {e}")
            # 실패해도 개별 ACL 처리로 진행
    
    # 3. 버킷 차단을 하지 않은 경우, 개별 ACL 처리
    print(f"\n  버킷 '{bucket}'의 퍼블릭 접근 문제 상세:")
    
    # 버킷 자체 ACL 문제가 있으면 처리
    if bucket_acl_issues:
        print(f"  └─ 버킷 ACL 문제: {len(bucket_acl_issues)}건")
        for issue in bucket_acl_issues:
            print(f"     • {issue['grantee_type']}에게 {issue['permission']} 권한")
        
        choice = input(f"  → 버킷 '{bucket}'의 퍼블릭 ACL을 제거하시겠습니까? (y/n): ").lower()
        if choice == 'y':
            _remove_bucket_acl(bucket)
    
    # 객체 ACL 문제들 처리
    if object_acl_issues:
        print(f"  └─ 객체 ACL 문제: {len(object_acl_issues)}건")
        choice = input(f"  → 개별 객체의 퍼블릭 ACL을 수정하시겠습니까? (y/n): ").lower()
        if choice == 'y':
            for idx, issue in enumerate(object_acl_issues, 1):
                key = issue['object']
                grantee_type = issue.get('grantee_type', '퍼블릭 접근자')
                permission = issue.get('permission', '')
                prompt = f"  → ({idx}/{len(object_acl_issues)}) 객체 '{bucket}/{key}'의 {grantee_type}에게 부여된 '{permission}' ACL을 제거(y/n): "
                obj_choice = input(prompt).lower()
                if obj_choice == 'y':
                    _remove_object_acl(bucket, key, issue)

def _remove_bucket_acl(bucket):
    try:
        s3 = boto3.client('s3')
        acl = s3.get_bucket_acl(Bucket=bucket)
        grants = [g for g in acl['Grants'] if g.get('Grantee', {}).get('URI', '') not in [
            'http://acs.amazonaws.com/groups/global/AllUsers',
            'http://acs.amazonaws.com/groups/global/AuthenticatedUsers'
        ]]
        s3.put_bucket_acl(Bucket=bucket, AccessControlPolicy={'Owner': acl['Owner'], 'Grants': grants})
        print(f"  ✅ 버킷 '{bucket}' 퍼블릭 ACL 제거 완료")
    except ClientError as e:
        print(f"  ❌ 버킷 '{bucket}' ACL 제거 실패: {e}")

def _remove_object_acl(bucket, key, issue):
    try:
        s3 = boto3.client('s3')
        acl = s3.get_object_acl(Bucket=bucket, Key=key)
        new_grants = []
        for grant in acl['Grants']:
            grantee = grant.get('Grantee', {})
            uri = grantee.get('URI', '')
            if grantee.get('Type') == 'Group' and (
                'AllUsers' in uri or 'AuthenticatedUsers' in uri):
                continue
            new_grants.append(grant)

        if len(new_grants) == len(acl['Grants']):
            print(f"  [SKIP] 객체 '{bucket}/{key}'의 퍼블릭 ACL이 이미 제거됨")
            return

        s3.put_object_acl(Bucket=bucket, Key=key, AccessControlPolicy={'Owner': acl['Owner'], 'Grants': new_grants})
        print(f"  ✅ 객체 '{bucket}/{key}' ACL 제거 완료")
    except ClientError as e:
        print(f"  ❌ 객체 '{bucket}/{key}' ACL 제거 실패: {e}")

if __name__ == "__main__":
    findings = check()
    if findings:
        fix(findings)