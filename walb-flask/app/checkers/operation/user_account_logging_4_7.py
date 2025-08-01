"""
[4.7] AWS 사용자 계정 접근 로깅 설정 체커
원본: SHIELDUS-AWS-CHECKER/operation/4_7_user_account_logging.py
"""

import boto3
import json
from datetime import datetime, timezone
from botocore.exceptions import ClientError
from app.checkers.base_checker import BaseChecker


class UserAccountLoggingChecker(BaseChecker):
    def __init__(self, session=None):
        super().__init__(session)
        
    @property
    def item_code(self):
        return "4.7"
    
    @property 
    def item_name(self):
        return "AWS 사용자 계정 접근 로깅 설정"
        
    def run_diagnosis(self):
        """
        [4.7] AWS 사용자 계정 접근 로깅 설정
        - 멀티 리전 + 관리 이벤트 포함한 CloudTrail 추적이 하나라도 존재하는지 점검
        """
        print("[INFO] 4.7 사용자 계정 접근 로깅 설정 체크 중...")
        cloudtrail = self.session.client('cloudtrail')
        trails_with_mgmt_events = []

        try:
            trails = cloudtrail.describe_trails()['trailList']
            for trail in trails:
                name = trail['Name']
                is_multi = trail.get('IsMultiRegionTrail')
                is_logging = cloudtrail.get_trail_status(Name=name).get('IsLogging')

                try:
                    selectors = cloudtrail.get_event_selectors(TrailName=name).get('EventSelectors', [])
                    has_mgmt = any(sel.get('IncludeManagementEvents') for sel in selectors)
                except:
                    has_mgmt = False

                if is_multi and is_logging and has_mgmt:
                    trails_with_mgmt_events.append(name)

            if trails_with_mgmt_events:
                print("[✓ COMPLIANT] 4.7 조건을 만족하는 CloudTrail 추적이 존재합니다.")
                for t in trails_with_mgmt_events:
                    print(f"  ├─ {t}")
                
                has_issues = False
                risk_level = 'low'
                message = "조건을 만족하는 CloudTrail 추적이 존재합니다"
            else:
                print("[⚠ WARNING] 4.7 조건을 만족하는 CloudTrail이 존재하지 않습니다.")
                
                has_issues = True
                risk_level = 'high'  # 로깅 미설정은 높은 위험도
                message = "조건을 만족하는 CloudTrail이 존재하지 않습니다"

            return {
                'status': 'success',
                'has_issues': has_issues,
                'risk_level': risk_level,
                'message': message,
                'trails_with_mgmt_events': trails_with_mgmt_events,
                'compliant_trail_exists': len(trails_with_mgmt_events) > 0,
                'summary': f"멀티 리전 + 관리 이벤트 포함 CloudTrail {len(trails_with_mgmt_events)}개 존재" if trails_with_mgmt_events else "조건을 만족하는 CloudTrail이 없습니다.",
                'details': {
                    'total_compliant_trails': len(trails_with_mgmt_events),
                    'compliant_trail_names': trails_with_mgmt_events,
                    'requires_setup': not bool(trails_with_mgmt_events)
                }
            }

        except ClientError as e:
            print(f"[ERROR] CloudTrail 조회 중 오류 발생: {e}")
            return {
                'status': 'error',
                'error_message': f"CloudTrail 조회 중 오류 발생: {str(e)}"
            }

    def execute_fix(self, selected_items):
        """
        [4.7] AWS 사용자 계정 접근 로깅 설정 조치
        - 멀티 리전 + 관리 이벤트 포함 CloudTrail 자동 생성
        - S3 버킷도 함께 생성 (timestamp 포함 이름), 정책 포함
        """
        if not selected_items:
            return {'status': 'no_action', 'message': '선택된 항목이 없습니다.'}

        # 진단 재실행으로 최신 데이터 확보
        diagnosis_result = self.run_diagnosis()
        if diagnosis_result['status'] != 'success':
            return {'status': 'error', 'message': '진단 실행 중 오류가 발생했습니다.'}
        
        if diagnosis_result.get('compliant_trail_exists'):
            return {'status': 'no_action', 'message': '이미 조건을 만족하는 CloudTrail이 존재합니다.'}

        # CloudTrail 생성 진행
        cloudtrail = self.session.client('cloudtrail')
        s3 = self.session.client('s3')
        sts = self.session.client('sts')

        account_id = sts.get_caller_identity()['Account']
        region = boto3.session.Session().region_name
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')

        trail_name = f'project2-management-trail-{timestamp}'
        bucket_name = f'cloudtrail-logs-project2-{timestamp}'

        results = []

        # S3 버킷 생성
        print(f"[INFO] S3 버킷 생성 중: {bucket_name}")
        try:
            if region == 'us-east-1':
                s3.create_bucket(Bucket=bucket_name)
            else:
                s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': region}
                )
            print("  └─ 생성 완료")

            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "AWSCloudTrailAclCheck",
                        "Effect": "Allow",
                        "Principal": {"Service": "cloudtrail.amazonaws.com"},
                        "Action": "s3:GetBucketAcl",
                        "Resource": f"arn:aws:s3:::{bucket_name}"
                    },
                    {
                        "Sid": "AWSCloudTrailWrite",
                        "Effect": "Allow",
                        "Principal": {"Service": "cloudtrail.amazonaws.com"},
                        "Action": "s3:PutObject",
                        "Resource": f"arn:aws:s3:::{bucket_name}/AWSLogs/{account_id}/*",
                        "Condition": {
                            "StringEquals": {
                                "s3:x-amz-acl": "bucket-owner-full-control"
                            }
                        }
                    }
                ]
            }

            s3.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(policy))
            print("  └─ S3 버킷 정책 설정 완료")
            
            results.append({
                'status': 'success',
                'resource': f"S3 Bucket {bucket_name}",
                'action': 'CloudTrail 로그 버킷 생성',
                'message': f"S3 버킷 '{bucket_name}' 생성 및 정책 설정 완료"
            })

        except ClientError as e:
            print(f"  └─ [ERROR] S3 버킷 생성 또는 정책 설정 실패: {e}")
            results.append({
                'status': 'error',
                'resource': f"S3 Bucket {bucket_name}",
                'error': str(e),
                'message': f"S3 버킷 생성 실패: {str(e)}"
            })
            return {
                'status': 'error',
                'results': results,
                'message': 'S3 버킷 생성 실패로 인해 CloudTrail 생성을 중단합니다.'
            }

        # CloudTrail 생성
        try:
            print(f"[INFO] CloudTrail 추적 생성 중: {trail_name}")
            cloudtrail.create_trail(
                Name=trail_name,
                S3BucketName=bucket_name,
                IsMultiRegionTrail=True,
                IncludeGlobalServiceEvents=True
            )

            cloudtrail.start_logging(Name=trail_name)

            cloudtrail.put_event_selectors(
                TrailName=trail_name,
                EventSelectors=[{
                    'ReadWriteType': 'All',
                    'IncludeManagementEvents': True,
                    'DataResources': []
                }]
            )

            print(f"[SUCCESS] 멀티 리전 CloudTrail '{trail_name}' 생성 완료 (관리 이벤트 포함)")
            results.append({
                'status': 'success',
                'resource': f"CloudTrail {trail_name}",
                'action': '멀티 리전 CloudTrail 생성',
                'message': f"CloudTrail '{trail_name}' 생성 완료 (관리 이벤트 포함)"
            })

        except ClientError as e:
            print(f"[ERROR] CloudTrail 생성 실패: {e}")
            results.append({
                'status': 'error',
                'resource': f"CloudTrail {trail_name}",
                'error': str(e),
                'message': f"CloudTrail 생성 실패: {str(e)}"
            })

        success_count = len([r for r in results if r['status'] == 'success'])
        return {
            'status': 'success' if success_count > 0 else 'error',
            'results': results,
            'message': f"{len(results)}개 항목에 대한 조치가 완료되었습니다."
        }

    def _get_fix_options(self, diagnosis_result):
        """자동 조치 옵션 반환"""
        if diagnosis_result.get('compliant_trail_exists'):
            return []
            
        return [{
            'id': 'create_management_trail',
            'title': '멀티 리전 CloudTrail 생성',
            'description': '관리 이벤트 포함 멀티 리전 CloudTrail과 전용 S3 버킷을 자동 생성합니다.',
            'items': [
                {
                    'id': 'create_trail_and_bucket',
                    'name': 'CloudTrail + S3 버킷 생성',
                    'description': '멀티 리전 CloudTrail과 로그 저장용 S3 버킷을 함께 생성'
                }
            ]
        }]