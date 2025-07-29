"""
[4.10] S3 버킷 로깅 설정 체커
원본: SHIELDUS-AWS-CHECKER/operation/4_10_s3_bucket_logging.py
"""

import boto3
import time
from botocore.exceptions import ClientError
from app.checkers.base_checker import BaseChecker


class S3BucketLoggingChecker(BaseChecker):
    def __init__(self, session=None):
        super().__init__(session)
        
    @property
    def item_code(self):
        return "4.10"
    
    @property 
    def item_name(self):
        return "S3 버킷 로깅 설정"
        
    def run_diagnosis(self):
        """
        [4.10] CloudTrail 로그 버킷의 서버 액세스 로깅 점검
        - CloudTrail에서 사용하는 S3 버킷의 서버 액세스 로깅 설정 여부 확인
        """
        print("[INFO] 4.10 CloudTrail 로그 버킷의 서버 액세스 로깅 점검을 시작합니다.")
        
        try:
            ct_buckets = self._check_cloudtrail_s3_buckets()

            if not ct_buckets:
                print("[INFO] CloudTrail 로그 저장 버킷이 없습니다.")
                return {
                    'status': 'success',
                    'has_issues': False,
                    'risk_level': 'low',
                    'message': 'CloudTrail 로그 저장 버킷이 없습니다.',
                    'insecure_buckets': [],
                    'summary': 'CloudTrail 로그 저장 버킷이 없습니다.',
                    'details': {
                        'total_cloudtrail_buckets': 0,
                        'insecure_buckets_count': 0
                    }
                }

            insecure_buckets = []
            for bucket in ct_buckets:
                if not self._check_logging_enabled(bucket):
                    insecure_buckets.append(bucket)

            if not insecure_buckets:
                print("[✓ COMPLIANT] 모든 CloudTrail 로그 버킷에 서버 액세스 로깅이 활성화되어 있습니다.")
                has_issues = False
                message = "모든 CloudTrail 로그 버킷에 서버 액세스 로깅이 활성화되어 있습니다."
            else:
                print(f"[⚠ WARNING] 다음 버킷들은 서버 액세스 로깅이 설정되어 있지 않습니다 ({len(insecure_buckets)}개):")
                for b in insecure_buckets:
                    print(f"  ├─ {b}")
                has_issues = True
                message = f"서버 액세스 로깅이 미설정된 CloudTrail 버킷 {len(insecure_buckets)}개 발견"

            risk_level = self.calculate_risk_level(len(insecure_buckets))
            
            return {
                'status': 'success',
                'has_issues': has_issues,
                'risk_level': risk_level,
                'message': message,
                'insecure_buckets': insecure_buckets,
                'cloudtrail_buckets': ct_buckets,
                'summary': f"서버 액세스 로깅 미설정 버킷 {len(insecure_buckets)}개" if has_issues else "모든 CloudTrail 로그 버킷에 로깅이 설정되어 있습니다.",
                'details': {
                    'total_cloudtrail_buckets': len(ct_buckets),
                    'insecure_buckets_count': len(insecure_buckets)
                }
            }

        except Exception as e:
            print(f"[ERROR] S3 버킷 로깅 점검 중 오류 발생: {e}")
            return {
                'status': 'error',
                'error_message': f"S3 버킷 로깅 점검 중 오류 발생: {str(e)}"
            }

    def _check_cloudtrail_s3_buckets(self):
        """CloudTrail이 사용하는 S3 버킷 목록 반환"""
        ct = self.session.client('cloudtrail')
        try:
            trails = ct.describe_trails()['trailList']
            return list(set([t['S3BucketName'] for t in trails if 'S3BucketName' in t]))
        except ClientError as e:
            print(f"[ERROR] CloudTrail 설정 조회 실패: {e}")
            return []

    def _check_logging_enabled(self, bucket_name):
        """S3 버킷의 서버 액세스 로깅 활성화 여부 확인"""
        s3 = self.session.client('s3')
        try:
            response = s3.get_bucket_logging(Bucket=bucket_name)
            return 'LoggingEnabled' in response
        except ClientError as e:
            print(f"[ERROR] '{bucket_name}'의 로깅 상태 확인 실패: {e}")
            return False

    def execute_fix(self, selected_items):
        """
        [4.10] S3 서버 액세스 로깅 설정 조치
        - CloudTrail 로그 버킷에 서버 액세스 로깅 활성화
        """
        if not selected_items:
            return {'status': 'no_action', 'message': '선택된 항목이 없습니다.'}

        # 진단 재실행으로 최신 데이터 확보
        diagnosis_result = self.run_diagnosis()
        if diagnosis_result['status'] != 'success' or not diagnosis_result.get('insecure_buckets'):
            return {'status': 'no_action', 'message': 'S3 버킷 로깅 조치가 필요한 항목이 없습니다.'}

        insecure_buckets = diagnosis_result['insecure_buckets']
        results = []
        
        print("[FIX] 서버 액세스 로깅 미설정 버킷에 대한 조치를 시작합니다.")

        # 로그 저장용 버킷 생성
        region = boto3.session.Session().region_name
        target_bucket = self._create_log_bucket(region)
        
        if not target_bucket:
            return {
                'status': 'error',
                'message': '로그 저장용 버킷 생성에 실패했습니다.'
            }

        for bucket_name in insecure_buckets:
            # 선택된 항목인지 확인
            if any(bucket_name in str(item) for item in selected_items.values() for item in item):
                # 이미 로깅이 활성화되어 있는지 다시 확인
                if self._check_logging_enabled(bucket_name):
                    print(f"     [INFO] '{bucket_name}' 버킷은 이미 로깅이 설정되어 있습니다.")
                    continue
                
                if bucket_name == target_bucket:
                    print(f"     [SKIP] '{bucket_name}' 버킷이 자기 자신을 대상으로 지정할 수 없습니다.")
                    results.append({
                        'status': 'skipped',
                        'resource': f"S3 Bucket {bucket_name}",
                        'message': f"'{bucket_name}' 버킷이 자기 자신을 대상으로 지정할 수 없어 건너뜁니다."
                    })
                    continue
                    
                try:
                    self._enable_access_logging(bucket_name, target_bucket)
                    print(f"     [SUCCESS] '{bucket_name}'의 서버 액세스 로깅을 '{target_bucket}'으로 설정했습니다.")
                    results.append({
                        'status': 'success',
                        'resource': f"S3 Bucket {bucket_name}",
                        'action': f"서버 액세스 로깅 활성화",
                        'message': f"'{bucket_name}'의 서버 액세스 로깅을 '{target_bucket}'으로 설정했습니다."
                    })
                except Exception as e:
                    print(f"     [ERROR] '{bucket_name}' 설정 실패: {e}")
                    results.append({
                        'status': 'error',
                        'resource': f"S3 Bucket {bucket_name}",
                        'error': str(e),
                        'message': f"'{bucket_name}' 서버 액세스 로깅 설정 실패: {str(e)}"
                    })
            else:
                print(f"     [INFO] '{bucket_name}' 버킷 로깅 설정을 건너뜁니다.")

        return {
            'status': 'success',
            'results': results,
            'message': f"{len(results)}개 항목에 대한 조치가 완료되었습니다."
        }

    def _create_log_bucket(self, region):
        """로그 저장용 S3 버킷 생성"""
        s3 = self.session.client('s3')
        timestamp = time.strftime('%Y%m%d%H%M%S')
        bucket_name = f'cloudtrail-access-logs-{timestamp}'
        
        try:
            if region == 'us-east-1':
                s3.create_bucket(Bucket=bucket_name)
            else:
                s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': region}
                )
            print(f"[SUCCESS] 로그 저장용 버킷 '{bucket_name}'을 생성했습니다.")
            return bucket_name
        except ClientError as e:
            print(f"[ERROR] 버킷 생성 실패: {e}")
            return None

    def _enable_access_logging(self, source_bucket, target_bucket):
        """S3 버킷에 서버 액세스 로깅 활성화"""
        s3 = self.session.client('s3')
        s3.put_bucket_logging(
            Bucket=source_bucket,
            BucketLoggingStatus={
                'LoggingEnabled': {
                    'TargetBucket': target_bucket,
                    'TargetPrefix': f'{source_bucket}/'
                }
            }
        )

    def _get_manual_guide(self, insecure_buckets=None):
        """S3 서버 액세스 로깅 수동 조치 가이드 반환"""
        if insecure_buckets is None:
            insecure_buckets = []
            
        return {
            'title': 'S3 서버 액세스 로깅 수동 조치 가이드',
            'description': 'CloudTrail 로그 버킷에 서버 액세스 로깅을 설정하여 버킷 접근 기록을 모니터링할 수 있습니다.',
            'steps': [
                {
                    'type': 'warning',
                    'title': '[주의] 로그 저장 버킷 분리',
                    'content': '서버 액세스 로그는 반드시 별도의 버킷에 저장해야 하며, 자기 자신에게 로깅할 수 없습니다.'
                },
                {
                    'type': 'step',
                    'title': '1. 로그 저장용 버킷 생성',
                    'content': '서버 액세스 로그를 저장할 별도의 S3 버킷을 생성합니다.'
                },
                {
                    'type': 'commands',
                    'title': 'AWS CLI로 로그 버킷 생성',
                    'content': [
                        '# 로그 저장용 버킷 생성',
                        'aws s3 mb s3://cloudtrail-access-logs-$(date +%Y%m%d%H%M%S)',
                        '',
                        '# 버킷 정책 설정 (Log Delivery Group 권한 부여)',
                        'aws s3api put-bucket-acl \\',
                        '  --bucket cloudtrail-access-logs-TIMESTAMP \\',
                        '  --grant-write URI=http://acs.amazonaws.com/groups/s3/LogDelivery \\',
                        '  --grant-read-acp URI=http://acs.amazonaws.com/groups/s3/LogDelivery'
                    ]
                },
                {
                    'type': 'step',
                    'title': '2. 서버 액세스 로깅 활성화',
                    'content': 'CloudTrail 버킷에서 서버 액세스 로깅을 활성화하고 대상 버킷을 지정합니다.'
                },
                {
                    'type': 'commands',
                    'title': '서버 액세스 로깅 설정',
                    'content': [
                        '# 서버 액세스 로깅 활성화',
                        'aws s3api put-bucket-logging \\',
                        '  --bucket <CLOUDTRAIL_BUCKET_NAME> \\',
                        '  --bucket-logging-status file://logging-config.json',
                        '',
                        '# logging-config.json 파일 내용:',
                        '{',
                        '  "LoggingEnabled": {',
                        '    "TargetBucket": "cloudtrail-access-logs-TIMESTAMP",',
                        '    "TargetPrefix": "access-logs/"',
                        '  }',
                        '}'
                    ]
                },
                {
                    'type': 'step',
                    'title': '3. 로그 분석 및 모니터링',
                    'content': '생성된 액세스 로그를 정기적으로 분석하여 비정상적인 접근을 모니터링합니다.'
                },
                {
                    'type': 'info',
                    'title': f'[참고] 조치 대상 버킷 ({len(insecure_buckets)}개)',
                    'content': f"다음 CloudTrail 버킷들에 대해 조치가 필요합니다: {', '.join(insecure_buckets[:5])}" + (f" 외 {len(insecure_buckets) - 5}개 더" if len(insecure_buckets) > 5 else "")
                }
            ]
        }

    def get_fix_options(self, diagnosis_result):
        """자동 조치 옵션 반환"""
        if not diagnosis_result.get('insecure_buckets'):
            return []
            
        insecure_buckets = diagnosis_result.get('insecure_buckets', [])
        
        return [{
            'id': 'enable_s3_access_logging',
            'title': 'S3 서버 액세스 로깅 활성화',
            'description': f'{len(insecure_buckets)}개의 CloudTrail 버킷에 서버 액세스 로깅을 자동으로 설정합니다. (로그 저장용 버킷 자동 생성)',
            'items': [
                {
                    'id': bucket_name,
                    'name': f"S3 버킷 {bucket_name}",
                    'description': "서버 액세스 로깅 미설정 - 자동 활성화 예정"
                }
                for bucket_name in insecure_buckets
            ]
        }]

    @property
    def item_code(self):
        return "4.10"
    
    @property
    def item_name(self):
        return "S3 버킷 로깅 설정"