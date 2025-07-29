"""
[4.3] S3 암호화 설정 체커
원본: SHIELDUS-AWS-CHECKER/operation/4_3_s3_encryption.py
"""

import boto3
from botocore.exceptions import ClientError
from app.checkers.base_checker import BaseChecker


class S3EncryptionChecker(BaseChecker):
    def __init__(self, session=None):
        super().__init__(session)
        
    @property
    def item_code(self):
        return "4.3"
    
    @property 
    def item_name(self):
        return "S3 암호화 설정"
        
    def run_diagnosis(self):
        """
        [4.3] S3 암호화 설정
        - S3 버킷에 기본 암호화가 설정되어 있는지 점검하고, 미설정 버킷 목록을 반환
        """
        print("[INFO] 4.3 S3 암호화 설정 체크 중...")
        s3 = self.session.client('s3')
        unencrypted_buckets = []

        try:
            buckets = s3.list_buckets()['Buckets']
            if not buckets:
                print("[✓ INFO] 4.3 점검할 S3 버킷이 존재하지 않습니다.")
                return {
                    'status': 'success',
                    'has_issues': False,
                    'risk_level': 'low',
                    'message': '점검할 S3 버킷이 존재하지 않습니다',
                    'unencrypted_buckets': [],
                    'summary': 'S3 버킷이 존재하지 않습니다.',
                    'details': {'total_buckets': 0, 'unencrypted_count': 0}
                }
            
            for bucket in buckets:
                bucket_name = bucket['Name']
                try:
                    s3.get_bucket_encryption(Bucket=bucket_name)
                except ClientError as e:
                    if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                        unencrypted_buckets.append(bucket_name)
            
            if not unencrypted_buckets:
                print("[✓ COMPLIANT] 4.3 모든 S3 버킷에 기본 암호화가 설정되어 있습니다.")
            else:
                print(f"[⚠ WARNING] 4.3 기본 암호화가 설정되지 않은 S3 버킷이 존재합니다 ({len(unencrypted_buckets)}개).")
                print(f"  ├─ 해당 버킷: {', '.join(unencrypted_buckets)}")

            has_issues = len(unencrypted_buckets) > 0
            risk_level = self.calculate_risk_level(len(unencrypted_buckets))
            
            return {
                'status': 'success',
                'has_issues': has_issues,
                'risk_level': risk_level,
                'message': f"기본 암호화가 설정되지 않은 S3 버킷 {len(unencrypted_buckets)}개 발견" if has_issues else "모든 S3 버킷에 기본 암호화가 설정되어 있습니다",
                'unencrypted_buckets': unencrypted_buckets,
                'summary': f"총 {len(unencrypted_buckets)}개의 미암호화 S3 버킷이 발견되었습니다." if has_issues else "모든 S3 버킷이 안전하게 암호화되어 있습니다.",
                'details': {
                    'total_buckets': len(buckets),
                    'unencrypted_count': len(unencrypted_buckets),
                    'encrypted_count': len(buckets) - len(unencrypted_buckets)
                }
            }

        except ClientError as e:
            print(f"[ERROR] S3 버킷 목록을 가져오는 중 오류 발생: {e}")
            return {
                'status': 'error',
                'error_message': f"S3 버킷 목록을 가져오는 중 오류 발생: {str(e)}"
            }

    def execute_fix(self, selected_items):
        """
        [4.3] S3 암호화 설정 조치
        - 기본 암호화가 없는 버킷에 SSE-S3 암호화를 적용
        """
        if not selected_items:
            return {'status': 'no_action', 'message': '선택된 항목이 없습니다.'}

        # 진단 재실행으로 최신 데이터 확보
        diagnosis_result = self.run_diagnosis()
        if diagnosis_result['status'] != 'success' or not diagnosis_result.get('unencrypted_buckets'):
            return {'status': 'no_action', 'message': 'S3 암호화 조치가 필요한 버킷이 없습니다.'}

        unencrypted_buckets = diagnosis_result['unencrypted_buckets']
        s3 = self.session.client('s3')
        results = []
        
        print("[FIX] 4.3 기본 암호화가 없는 S3 버킷에 대한 조치를 시작합니다.")
        
        for bucket_name in unencrypted_buckets:
            # 선택된 항목인지 확인
            if any(bucket_name in str(item) for item in selected_items.values() for item in item):
                try:
                    s3.put_bucket_encryption(
                        Bucket=bucket_name,
                        ServerSideEncryptionConfiguration={
                            'Rules': [{
                                'ApplyServerSideEncryptionByDefault': {
                                    'SSEAlgorithm': 'AES256'
                                }
                            }]
                        }
                    )
                    print(f"     [SUCCESS] 버킷 '{bucket_name}'에 SSE-S3 기본 암호화를 적용했습니다.")
                    results.append({
                        'status': 'success',
                        'resource': f"S3 Bucket {bucket_name}",
                        'action': 'SSE-S3 기본 암호화 적용',
                        'message': f"버킷 '{bucket_name}'에 SSE-S3 기본 암호화를 적용했습니다."
                    })
                    
                except ClientError as e:
                    print(f"     [ERROR] 암호화 적용 실패: {e}")
                    results.append({
                        'status': 'error',
                        'resource': f"S3 Bucket {bucket_name}",
                        'error': str(e),
                        'message': f"버킷 '{bucket_name}' 암호화 적용 실패: {str(e)}"
                    })
            else:
                print(f"     [INFO] 버킷 '{bucket_name}' 암호화 적용을 건너뜁니다.")

        return {
            'status': 'success',
            'results': results,
            'message': f"{len(results)}개 항목에 대한 조치가 완료되었습니다."
        }

    def get_fix_options(self, diagnosis_result):
        """자동 조치 옵션 반환"""
        if not diagnosis_result.get('unencrypted_buckets'):
            return []
            
        unencrypted_buckets = diagnosis_result.get('unencrypted_buckets', [])
        
        return [{
            'id': 'apply_sse_s3_encryption',
            'title': 'S3 버킷 기본 암호화 적용',
            'description': '기본 암호화가 설정되지 않은 S3 버킷에 SSE-S3 암호화를 적용합니다.',
            'items': [
                {
                    'id': bucket_name,
                    'name': f"S3 버킷 {bucket_name}",
                    'description': f"기본 암호화 미설정 - SSE-S3 적용 예정"
                }
                for bucket_name in unencrypted_buckets
            ]
        }]