import boto3
from botocore.exceptions import ClientError

def check():
    """
    [3.7] S3 버킷/객체 접근 관리
    - 1단계: 계정 수준의 퍼블릭 액세스 차단 확인 (최우선)
    - 2단계: 계정 차단이 비활성화된 경우, 개별 버킷/객체 ACL 상세 점검
    """
    print("[INFO] 3.7 S3 버킷/객체 접근 관리 체크 중...")
    s3_control = boto3.client('s3control')
    s3 = boto3.client('s3')
    sts = boto3.client('sts')
    findings = {
        'account_block_off': False, 
        'bucket_acl_issues': [],
        'object_acl_issues': []
    }

    try:
        account_id = sts.get_caller_identity()['Account']
        
        # ========== 1단계: 계정 수준 퍼블릭 액세스 차단 확인 ==========
        print("[INFO] 1단계: 계정 수준 퍼블릭 액세스 차단 설정 확인 중...")
        
        try:
            pab_config = s3_control.get_public_access_block(AccountId=account_id)['PublicAccessBlockConfiguration']
            
            # 모든 차단 설정이 True인지 확인
            all_blocked = all([
                pab_config.get('BlockPublicAcls', False),
                pab_config.get('IgnorePublicAcls', False),
                pab_config.get('BlockPublicPolicy', False),
                pab_config.get('RestrictPublicBuckets', False)
            ])
            
            if all_blocked:
                print("[✅ 안전] 계정 수준의 '모든 퍼블릭 액세스 차단'이 완전히 활성화되어 있습니다.")
                print("  └─ 모든 S3 리소스가 퍼블릭 액세스로부터 보호됩니다.")
                return {}  # 안전하므로 추가 점검 불필요
            else:
                findings['account_block_off'] = True
                disabled_settings = []
                if not pab_config.get('BlockPublicAcls'): disabled_settings.append('BlockPublicAcls')
                if not pab_config.get('IgnorePublicAcls'): disabled_settings.append('IgnorePublicAcls')  
                if not pab_config.get('BlockPublicPolicy'): disabled_settings.append('BlockPublicPolicy')
                if not pab_config.get('RestrictPublicBuckets'): disabled_settings.append('RestrictPublicBuckets')
                
                print(f"[⚠ 위험] 계정 수준 퍼블릭 액세스 차단에서 일부 설정이 비활성화되어 있습니다.")
                print(f"  ├─ 비활성화된 설정: {', '.join(disabled_settings)}")
                print(f"  └─ 개별 버킷/객체 ACL 상세 점검을 진행합니다...")
                
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchPublicAccessBlockConfiguration':
                findings['account_block_off'] = True
                print("[⚠ 위험] 계정 수준의 퍼블릭 액세스 차단이 전혀 설정되어 있지 않습니다.")
                print("  └─ 개별 버킷/객체 ACL 상세 점검을 진행합니다...")
            else:
                print(f"[ERROR] 계정 수준 설정 확인 중 오류: {e}")
                return {}

        # ========== 2단계: 개별 버킷 및 객체 ACL 상세 점검 ==========
        if findings['account_block_off']:
            print("\n[INFO] 2단계: 개별 S3 버킷 및 객체 ACL 점검 중...")
            
            bucket_list = s3.list_buckets()['Buckets']
            if not bucket_list:
                print("[INFO] 계정에 S3 버킷이 없습니다.")
                return findings
                
            print(f"[INFO] 총 {len(bucket_list)}개 버킷을 점검합니다...")
            
            for bucket in bucket_list:
                bucket_name = bucket['Name']
                print(f"  └─ 점검 중: {bucket_name}")
                
                # 2-1. 버킷 레벨 ACL 점검
                bucket_public_acl = _check_bucket_acl(s3, bucket_name)
                if bucket_public_acl:
                    findings['bucket_acl_issues'].extend(bucket_public_acl)
                
                # 2-2. 버킷 내 객체 ACL 점검 (샘플링)
                object_acl_issues = _check_object_acls(s3, bucket_name)
                if object_acl_issues:
                    findings['object_acl_issues'].extend(object_acl_issues)

        # ========== 결과 요약 출력 ==========
        _print_findings_summary(findings)
        
        return findings if any(findings.values()) else {}
            
    except ClientError as e:
        print(f"[ERROR] S3 점검 중 오류 발생: {e}")
        return {}

def _check_bucket_acl(s3, bucket_name):
    """
    개별 버킷의 ACL을 점검하여 퍼블릭 권한 확인
    """
    bucket_issues = []
    
    try:
        acl = s3.get_bucket_acl(Bucket=bucket_name)
        
        for grant in acl['Grants']:
            grantee = grant.get('Grantee', {})
            permission = grant.get('Permission')
            
            if grantee.get('Type') == 'Group':
                uri = grantee.get('URI', '')
                if 'AllUsers' in uri:
                    bucket_issues.append({
                        'type': 'bucket_acl',
                        'bucket': bucket_name,
                        'grantee_type': 'AllUsers (모든 사람)',
                        'permission': permission,
                        'risk_level': 'HIGH'
                    })
                elif 'AuthenticatedUsers' in uri:
                    bucket_issues.append({
                        'type': 'bucket_acl', 
                        'bucket': bucket_name,
                        'grantee_type': 'AuthenticatedUsers (인증된 사용자)',
                        'permission': permission,
                        'risk_level': 'MEDIUM'
                    })
        
    except ClientError as e:
        print(f"    [WARNING] 버킷 '{bucket_name}' ACL 확인 실패: {e}")
    
    return bucket_issues

def _check_object_acls(s3, bucket_name, max_objects=10):
    """
    버킷 내 객체들의 ACL을 샘플링하여 점검 (최대 10개)
    """
    object_issues = []
    
    try:
        # 버킷 내 객체 목록 조회 (최대 max_objects개)
        paginator = s3.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=bucket_name, PaginationConfig={'MaxItems': max_objects})
        
        object_count = 0
        for page in page_iterator:
            for obj in page.get('Contents', []):
                object_key = obj['Key']
                object_count += 1
                
                try:
                    # 객체 ACL 확인
                    obj_acl = s3.get_object_acl(Bucket=bucket_name, Key=object_key)
                    
                    for grant in obj_acl['Grants']:
                        grantee = grant.get('Grantee', {})
                        permission = grant.get('Permission')
                        
                        if grantee.get('Type') == 'Group':
                            uri = grantee.get('URI', '')
                            if 'AllUsers' in uri:
                                object_issues.append({
                                    'type': 'object_acl',
                                    'bucket': bucket_name,
                                    'object': object_key,
                                    'grantee_type': 'AllUsers (모든 사람)',
                                    'permission': permission,
                                    'risk_level': 'HIGH'
                                })
                            elif 'AuthenticatedUsers' in uri:
                                object_issues.append({
                                    'type': 'object_acl',
                                    'bucket': bucket_name, 
                                    'object': object_key,
                                    'grantee_type': 'AuthenticatedUsers (인증된 사용자)',
                                    'permission': permission,
                                    'risk_level': 'MEDIUM'
                                })
                        
                except ClientError as e:
                    # 객체 ACL 확인 실패는 로그만 남기고 계속 진행
                    if 'AccessDenied' not in str(e):
                        print(f"    [WARNING] 객체 '{object_key}' ACL 확인 실패: {e}")
        
        if object_count > 0:
            print(f"    └─ 객체 ACL 점검 완료: {object_count}개 객체 확인")
                        
    except ClientError as e:
        print(f"    [WARNING] 버킷 '{bucket_name}' 객체 목록 조회 실패: {e}")
    
    return object_issues

def _print_findings_summary(findings):
    """
    점검 결과 요약 출력
    """
    print("\n" + "="*60)
    print("📊 S3 보안 점검 결과 요약")
    print("="*60)
    
    total_issues = len(findings.get('bucket_acl_issues', [])) + len(findings.get('object_acl_issues', []))
    
    if not any(findings.values()):
        print("[✅ 안전] 모든 S3 리소스가 보안 기준을 준수합니다.")
        return
    
    if findings.get('account_block_off'):
        print("[⚠ 중요] 계정 수준 퍼블릭 액세스 차단이 비활성화되어 있습니다.")
        
    if findings.get('bucket_acl_issues'):
        print(f"\n[🪣 버킷 ACL 문제] {len(findings['bucket_acl_issues'])}건 발견:")
        for issue in findings['bucket_acl_issues']:
            risk_emoji = "🔴" if issue['risk_level'] == 'HIGH' else "🟡"
            print(f"  {risk_emoji} 버킷 '{issue['bucket']}': {issue['grantee_type']}에게 {issue['permission']} 권한 부여")
    
    if findings.get('object_acl_issues'):
        print(f"\n[📄 객체 ACL 문제] {len(findings['object_acl_issues'])}건 발견:")
        for issue in findings['object_acl_issues'][:5]:  # 최대 5개만 표시
            risk_emoji = "🔴" if issue['risk_level'] == 'HIGH' else "🟡"
            print(f"  {risk_emoji} 객체 '{issue['bucket']}/{issue['object']}': {issue['grantee_type']}에게 {issue['permission']} 권한 부여")
        
        if len(findings['object_acl_issues']) > 5:
            print(f"  └─ ... 외 {len(findings['object_acl_issues']) - 5}건 더 있음")

def fix(findings):
    """
    [3.7] S3 버킷/객체 접근 관리 조치
    - 1순위: 계정 수준 퍼블릭 액세스 차단 활성화 (가장 효과적)
    - 2순위: 개별 버킷 ACL 수정
    - 3순위: 개별 객체 ACL 수정
    """
    if not findings:
        return

    print("\n" + "="*60)
    print("🔧 S3 보안 조치 시작")
    print("="*60)

    # ========== 1순위: 계정 수준 퍼블릭 액세스 차단 ==========
    if findings.get('account_block_off'):
        print("\n[1순위 조치] 계정 수준 퍼블릭 액세스 차단 설정")
        print("💡 이 조치만으로도 모든 S3 리소스가 안전해집니다.")
        
        choice = input("  → 계정 전체에 '모든 퍼블릭 액세스 차단'을 활성화하시겠습니까? (y/n): ").lower()
        if choice == 'y':
            if _apply_account_level_block():
                print("\n✅ 계정 수준 차단이 완료되어 추가 조치가 불필요합니다.")
                return

    # ========== 2순위: 개별 버킷 ACL 조치 ==========
    if findings.get('bucket_acl_issues'):
        print(f"\n[2순위 조치] 버킷 ACL 수정 ({len(findings['bucket_acl_issues'])}건)")
        
        for issue in findings['bucket_acl_issues']:
            bucket_name = issue['bucket']
            grantee_type = issue['grantee_type']
            
            choice = input(f"  → 버킷 '{bucket_name}'에서 '{grantee_type}' 권한을 제거하시겠습니까? (y/n): ").lower()
            if choice == 'y':
                _remove_bucket_public_acl(bucket_name, issue)

    # ========== 3순위: 버킷별 퍼블릭 액세스 차단 ==========
    if findings.get('bucket_acl_issues') or findings.get('object_acl_issues'):
        print(f"\n[3순위 조치] 버킷별 퍼블릭 액세스 차단 설정")
        print("💡 특정 버킷에만 퍼블릭 액세스 차단을 적용할 수 있습니다.")
        
        # 문제가 있는 버킷들 추출
        problem_buckets = set()
        for issue in findings.get('bucket_acl_issues', []):
            problem_buckets.add(issue['bucket'])
        for issue in findings.get('object_acl_issues', []):
            problem_buckets.add(issue['bucket'])
        
        if problem_buckets:
            _apply_bucket_level_blocks(problem_buckets, findings)
        
    # ========== 4순위: 개별 객체 ACL 조치 ==========
    if findings.get('object_acl_issues'):
        print(f"\n[4순위 조치] 개별 객체 ACL 수정 ({len(findings['object_acl_issues'])}건)")
        print("⚠️ 주의: 이 방법은 시간이 오래 걸릴 수 있습니다.")
        
        remaining_choice = input("  → 남은 퍼블릭 객체 ACL을 개별적으로 수정하시겠습니까? (y/n): ").lower()
        if remaining_choice == 'y':
            _individual_fix_object_acls(findings['object_acl_issues'])

def _apply_account_level_block():
    """
    계정 수준 퍼블릭 액세스 차단 적용
    """
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
        print("  ✅ [SUCCESS] 계정 수준 퍼블릭 액세스 차단을 완전히 활성화했습니다.")
        return True
        
    except ClientError as e:
        print(f"  ❌ [ERROR] 계정 수준 차단 설정 실패: {e}")
        return False

def _remove_bucket_public_acl(bucket_name, issue):
    """
    버킷의 퍼블릭 ACL 제거
    """
    try:
        s3 = boto3.client('s3')
        
        # 현재 ACL 가져오기
        current_acl = s3.get_bucket_acl(Bucket=bucket_name)
        
        # 퍼블릭 권한만 제외한 새 ACL 생성
        new_grants = []
        for grant in current_acl['Grants']:
            grantee = grant.get('Grantee', {})
            if grantee.get('Type') == 'Group':
                uri = grantee.get('URI', '')
                if 'AllUsers' in uri or 'AuthenticatedUsers' in uri:
                    continue  # 퍼블릭 권한 제외
            new_grants.append(grant)
        
        # 새 ACL 적용
        s3.put_bucket_acl(
            Bucket=bucket_name,
            AccessControlPolicy={
                'Owner': current_acl['Owner'],
                'Grants': new_grants
            }
        )
        print(f"  ✅ [SUCCESS] 버킷 '{bucket_name}'의 퍼블릭 ACL을 제거했습니다.")
        
    except ClientError as e:
        print(f"  ❌ [ERROR] 버킷 '{bucket_name}' ACL 수정 실패: {e}")

def _apply_bucket_level_blocks(problem_buckets, findings):
    """
    개별 버킷에 퍼블릭 액세스 차단 적용
    """
    s3 = boto3.client('s3')
    
    print(f"  → 문제가 발견된 버킷: {', '.join(problem_buckets)}")
    
    for bucket_name in problem_buckets:
        # 해당 버킷의 문제 개수 계산
        bucket_issues = 0
        bucket_issues += len([x for x in findings.get('bucket_acl_issues', []) if x['bucket'] == bucket_name])
        bucket_issues += len([x for x in findings.get('object_acl_issues', []) if x['bucket'] == bucket_name])
        
        choice = input(f"  → 버킷 '{bucket_name}'에 '모든 퍼블릭 액세스 차단'을 적용하시겠습니까? (문제: {bucket_issues}건) (y/n): ").lower()
        if choice == 'y':
            if _apply_bucket_public_access_block(bucket_name):
                print(f"    ✅ 버킷 '{bucket_name}'의 모든 퍼블릭 액세스가 차단되었습니다.")
            else:
                print(f"    ❌ 버킷 '{bucket_name}' 차단 설정에 실패했습니다.")

def _apply_bucket_public_access_block(bucket_name):
    """
    특정 버킷에 퍼블릭 액세스 차단 적용
    """
    try:
        s3 = boto3.client('s3')
        
        s3.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': True
            }
        )
        return True
        
    except ClientError as e:
        print(f"    [ERROR] 버킷 '{bucket_name}' 퍼블릭 액세스 차단 실패: {e}")
        return False

def _batch_fix_object_acls(object_issues):
    """
    객체 ACL 일괄 수정
    """
    s3 = boto3.client('s3')
    
    # 버킷별로 그룹화
    buckets = {}
    for issue in object_issues:
        bucket = issue['bucket']
        if bucket not in buckets:
            buckets[bucket] = []
        buckets[bucket].append(issue)
    
    for bucket_name, issues in buckets.items():
        print(f"  → 버킷 '{bucket_name}' 내 {len(issues)}개 객체 ACL 수정 중...")
        
        success_count = 0
        for issue in issues:
            if _remove_object_public_acl(issue['bucket'], issue['object']):
                success_count += 1
        
        print(f"    ✅ {success_count}/{len(issues)}개 객체 ACL 수정 완료")

def _individual_fix_object_acls(object_issues):
    """
    객체 ACL 개별 수정
    """
    print("  💡 개별 객체 ACL 수정은 시간이 오래 걸릴 수 있습니다.")
    max_show = min(10, len(object_issues))
    
    for i, issue in enumerate(object_issues[:max_show]):
        choice = input(f"  → ({i+1}/{max_show}) 객체 '{issue['bucket']}/{issue['object']}'의 퍼블릭 ACL을 제거하시겠습니까? (y/n/q): ").lower()
        if choice == 'y':
            _remove_object_public_acl(issue['bucket'], issue['object'])
        elif choice == 'q':
            print("    [INFO] 사용자 요청으로 개별 수정을 중단합니다.")
            break
    
    if len(object_issues) > max_show:
        print(f"  [INFO] 남은 {len(object_issues) - max_show}개 객체는 버킷 수준 차단을 권장합니다.")

def _remove_object_public_acl(bucket_name, object_key):
    """
    개별 객체의 퍼블릭 ACL 제거
    """
    try:
        s3 = boto3.client('s3')
        
        # 현재 객체 ACL 가져오기
        current_acl = s3.get_object_acl(Bucket=bucket_name, Key=object_key)
        
        # 퍼블릭 권한만 제외한 새 ACL 생성
        new_grants = []
        for grant in current_acl['Grants']:
            grantee = grant.get('Grantee', {})
            if grantee.get('Type') == 'Group':
                uri = grantee.get('URI', '')
                if 'AllUsers' in uri or 'AuthenticatedUsers' in uri:
                    continue  # 퍼블릭 권한 제외
            new_grants.append(grant)
        
        # 새 ACL 적용
        s3.put_object_acl(
            Bucket=bucket_name,
            Key=object_key,
            AccessControlPolicy={
                'Owner': current_acl['Owner'],
                'Grants': new_grants
            }
        )
        return True
        
    except ClientError as e:
        print(f"    ❌ [ERROR] 객체 '{object_key}' ACL 수정 실패: {e}")
        return False

if __name__ == "__main__":
    findings_data = check()
    if findings_data:
        fix(findings_data)