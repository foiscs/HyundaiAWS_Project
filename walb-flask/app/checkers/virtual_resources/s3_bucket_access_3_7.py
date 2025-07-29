"""
[3.7] S3 버킷/객체 접근 관리 체커
원본: SHIELDUS-AWS-CHECKER/virtual_resources/3_7_s3_bucket_access.py
"""

import boto3
from botocore.exceptions import ClientError
from app.checkers.base_checker import BaseChecker


class S3BucketAccessChecker(BaseChecker):
    def __init__(self, session=None):
        super().__init__(session)
        
    @property
    def item_code(self):
        return "3.7"
    
    @property 
    def item_name(self):
        return "S3 버킷/객체 접근 관리"
        
    def run_diagnosis(self):
        """
        [3.7] S3 버킷/객체 접근 관리
        - 1단계: 계정 수준의 퍼블릭 액세스 차단 확인 (최우선)
        - 2단계: 계정 차단이 비활성화된 경우, 개별 버킷/객체 ACL 상세 점검
        """
        print("[INFO] 3.7 S3 버킷/객체 접근 관리 체크 중...")
        s3_control = self.session.client('s3control')
        s3 = self.session.client('s3')
        sts = self.session.client('sts')
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
                    return {
                        'status': 'success',
                        'has_issues': False,
                        'risk_level': 'low',
                        'message': '계정 수준의 모든 퍼블릭 액세스 차단이 활성화되어 있습니다',
                        'findings': findings,
                        'summary': '모든 S3 리소스가 퍼블릭 액세스로부터 보호됩니다.',
                        'details': {'account_level_protected': True}
                    }
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
                    return {
                        'status': 'error',
                        'error_message': f"계정 수준 설정 확인 중 오류: {str(e)}"
                    }

            # ========== 2단계: 개별 버킷 및 객체 ACL 상세 점검 ==========
            if findings['account_block_off']:
                print("\n[INFO] 2단계: 개별 S3 버킷 및 객체 ACL 점검 중...")
                
                bucket_list = s3.list_buckets()['Buckets']
                if not bucket_list:
                    print("[INFO] 계정에 S3 버킷이 없습니다.")
                else:
                    print(f"[INFO] 총 {len(bucket_list)}개 버킷을 점검합니다...")
                    
                    for bucket in bucket_list:
                        bucket_name = bucket['Name']
                        print(f"  └─ 점검 중: {bucket_name}")
                        
                        # 2-1. 버킷 레벨 ACL 점검
                        bucket_public_acl = self._check_bucket_acl(s3, bucket_name)
                        if bucket_public_acl:
                            findings['bucket_acl_issues'].extend(bucket_public_acl)
                        
                        # 2-2. 버킷 내 객체 ACL 점검 (샘플링)
                        object_acl_issues = self._check_object_acls(s3, bucket_name)
                        if object_acl_issues:
                            findings['object_acl_issues'].extend(object_acl_issues)

            # ========== 결과 요약 출력 ==========
            self._print_findings_summary(findings)
            
            has_issues = any(findings.values())
            total_issues = len(findings.get('bucket_acl_issues', [])) + len(findings.get('object_acl_issues', []))
            risk_level = self.calculate_risk_level(total_issues + (1 if findings.get('account_block_off') else 0))
            
            return {
                'status': 'success',
                'has_issues': has_issues,
                'risk_level': risk_level,
                'message': f"S3 보안 문제 {total_issues}건 발견" if has_issues else "모든 S3 리소스가 보안 기준을 준수합니다",
                'findings': findings,
                'summary': f"계정 수준 차단 미설정, 버킷 ACL 문제 {len(findings.get('bucket_acl_issues', []))}건, 객체 ACL 문제 {len(findings.get('object_acl_issues', []))}건" if has_issues else "모든 S3 리소스가 안전합니다.",
                'details': {
                    'account_block_off': findings.get('account_block_off', False),
                    'bucket_acl_issues': len(findings.get('bucket_acl_issues', [])),
                    'object_acl_issues': len(findings.get('object_acl_issues', [])),
                    'total_issues': total_issues
                }
            }
                
        except ClientError as e:
            print(f"[ERROR] S3 점검 중 오류 발생: {e}")
            return {
                'status': 'error',
                'error_message': f"S3 점검 중 오류 발생: {str(e)}"
            }

    def _check_bucket_acl(self, s3, bucket_name):
        """개별 버킷의 ACL을 점검하여 퍼블릭 권한 확인"""
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

    def _check_object_acls(self, s3, bucket_name, max_objects=10):
        """버킷 내 객체들의 ACL을 샘플링하여 점검 (최대 10개)"""
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

    def _print_findings_summary(self, findings):
        """점검 결과 요약 출력"""
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

    def execute_fix(self, selected_items):
        """
        [3.7] S3 버킷/객체 접근 관리 조치
        - 복잡한 수동 조치가 필요하므로 가이드 제공
        """
        if not selected_items:
            return {'status': 'no_action', 'message': '선택된 항목이 없습니다.'}

        # 진단 재실행으로 최신 데이터 확보
        diagnosis_result = self.run_diagnosis()
        if diagnosis_result['status'] != 'success' or not diagnosis_result.get('findings'):
            return {'status': 'no_action', 'message': 'S3 보안 조치가 필요한 항목이 없습니다.'}

        print("\n" + "="*60)
        print("🔧 S3 보안 조치 시작")
        print("="*60)

        return {
            'status': 'manual_required',
            'message': 'S3 버킷/객체 접근 관리는 복잡한 수동 조치가 필요합니다.',
            'manual_guide': self._get_manual_guide()
        }

    def _get_manual_guide(self):
        """수동 조치 가이드 반환"""
        return {
            'title': 'S3 버킷/객체 접근 관리 수동 조치 가이드',
            'description': 'S3 보안 설정은 데이터 접근에 큰 영향을 미치므로 단계별 신중한 조치가 필요합니다.',
            'steps': [
                {
                    'type': 'warning',
                    'title': '[주의] 자동 수정 불가',
                    'content': 'S3 접근 권한 변경은 애플리케이션 동작에 큰 영향을 미칠 수 있어 수동 조치만 지원합니다.'
                },
                {
                    'type': 'step',
                    'title': '1순위: 계정 수준 퍼블릭 액세스 차단',
                    'content': 'AWS 콘솔 > S3 > Block Public Access settings for this account에서 모든 옵션을 활성화하세요.'
                },
                {
                    'type': 'step',
                    'title': '2순위: 개별 버킷 퍼블릭 액세스 차단',
                    'content': '문제가 있는 각 버킷의 "Permissions" 탭에서 "Block public access" 설정을 활성화하세요.'
                },
                {
                    'type': 'step',
                    'title': '3순위: 버킷 ACL 수정',
                    'content': '버킷의 "Permissions" > "Access control list (ACL)" 에서 Public access 권한을 제거하세요.'
                },
                {
                    'type': 'step',
                    'title': '4순위: 개별 객체 ACL 수정',
                    'content': '시간이 오래 걸리므로, 버킷 수준 차단을 우선 적용하는 것을 권장합니다.'
                },
                {
                    'type': 'info',
                    'title': '[참고] 효과적인 S3 보안 관리',
                    'content': '계정 수준 차단 > 버킷 수준 차단 > 개별 ACL 순서로 적용하면 가장 안전하고 효율적입니다.'
                }
            ]
        }

    def get_fix_options(self, diagnosis_result):
        """수동 조치 옵션 반환"""
        if not diagnosis_result.get('findings') or not any(diagnosis_result['findings'].values()):
            return []
            
        findings = diagnosis_result.get('findings', {})
        
        return [{
            'id': 'manual_s3_security_fix',
            'title': 'S3 보안 설정 수동 조치',
            'description': 'S3 버킷/객체의 퍼블릭 액세스를 단계별로 차단합니다. (수동 조치 필요)',
            'is_manual': True,
            'items': [
                {
                    'id': 'account_level_block',
                    'name': '계정 수준 퍼블릭 액세스 차단',
                    'description': '모든 S3 리소스에 대한 퍼블릭 액세스를 계정 수준에서 차단'
                },
                {
                    'id': f'bucket_acl_issues_{len(findings.get("bucket_acl_issues", []))}',
                    'name': f'버킷 ACL 문제 ({len(findings.get("bucket_acl_issues", []))}건)',
                    'description': '개별 버킷의 퍼블릭 ACL 권한 제거'
                },
                {
                    'id': f'object_acl_issues_{len(findings.get("object_acl_issues", []))}',
                    'name': f'객체 ACL 문제 ({len(findings.get("object_acl_issues", []))}건)',
                    'description': '개별 객체의 퍼블릭 ACL 권한 제거'
                }
            ]
        }]