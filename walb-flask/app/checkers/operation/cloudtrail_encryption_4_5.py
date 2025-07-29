"""
[4.5] CloudTrail 암호화 설정 체커
원본: SHIELDUS-AWS-CHECKER/operation/4_5_cloudtrail_encryption.py
"""

import boto3
import json
from botocore.exceptions import ClientError
from app.checkers.base_checker import BaseChecker


class CloudtrailEncryptionChecker(BaseChecker):
    def __init__(self, session=None):
        super().__init__(session)
        
    @property
    def item_code(self):
        return "4.5"
    
    @property 
    def item_name(self):
        return "CloudTrail 암호화 설정"
        
    def run_diagnosis(self):
        """
        [4.5] CloudTrail 암호화 설정
        - CloudTrail 로그 파일 암호화에 SSE-KMS가 사용되는지 점검하고, 미적용된 Trail 목록 반환
        """
        print("[INFO] 4.5 CloudTrail 암호화 설정 체크 중...")
        cloudtrail = self.session.client('cloudtrail')
        not_kms_encrypted_trails = []
        trail_details = []

        try:
            trails = cloudtrail.describe_trails().get('trailList', [])
            if not trails:
                print("[INFO] 4.5 활성화된 CloudTrail이 없습니다.")
                return {
                    'status': 'success',
                    'has_issues': False,
                    'risk_level': 'low',
                    'message': '활성화된 CloudTrail이 없습니다',
                    'not_kms_encrypted_trails': [],
                    'trail_details': [],
                    'summary': 'CloudTrail이 존재하지 않습니다.',
                    'details': {'total_trails': 0, 'unencrypted_count': 0}
                }

            for trail in trails:
                trail_detail = {
                    'name': trail['Name'],
                    'has_kms': bool(trail.get('KmsKeyId')),
                    'kms_key_id': trail.get('KmsKeyId', ''),
                    'is_multi_region': trail.get('IsMultiRegionTrail', False)
                }
                trail_details.append(trail_detail)
                
                if not trail.get('KmsKeyId'):
                    not_kms_encrypted_trails.append(trail['Name'])

            if not not_kms_encrypted_trails:
                print("[✓ COMPLIANT] 4.5 모든 CloudTrail이 SSE-KMS로 암호화되어 있습니다.")
            else:
                print(f"[⚠ WARNING] 4.5 SSE-KMS 암호화가 적용되지 않은 CloudTrail이 존재합니다 ({len(not_kms_encrypted_trails)}개).")
                for group_name in not_kms_encrypted_trails[:5]: 
                    print(f"  ├─ {group_name}")
                if len(not_kms_encrypted_trails) > 5: 
                    print(f"  └─ ... 외 {len(not_kms_encrypted_trails) - 5}개 더 있음")

            has_issues = len(not_kms_encrypted_trails) > 0
            risk_level = self.calculate_risk_level(len(not_kms_encrypted_trails))
            
            return {
                'status': 'success',
                'has_issues': has_issues,
                'risk_level': risk_level,
                'message': f"SSE-KMS 암호화가 적용되지 않은 CloudTrail {len(not_kms_encrypted_trails)}개 발견" if has_issues else "모든 CloudTrail이 SSE-KMS로 암호화되어 있습니다",
                'not_kms_encrypted_trails': not_kms_encrypted_trails,
                'trail_details': trail_details,
                'summary': f"총 {len(not_kms_encrypted_trails)}개의 미암호화 CloudTrail이 발견되었습니다." if has_issues else "모든 CloudTrail이 안전하게 암호화되어 있습니다.",
                'details': {
                    'total_trails': len(trails),
                    'unencrypted_count': len(not_kms_encrypted_trails),
                    'encrypted_count': len(trails) - len(not_kms_encrypted_trails)
                }
            }

        except ClientError as e:
            print(f"[ERROR] CloudTrail 정보를 가져오는 중 오류 발생: {e}")
            return {
                'status': 'error',
                'error_message': f"CloudTrail 정보를 가져오는 중 오류 발생: {str(e)}"
            }

    def execute_fix(self, selected_items):
        """
        [4.5] CloudTrail 암호화 설정 조치
        - KMS 암호화가 없는 Trail에 대해 사용자 확인 후 KMS 암호화 적용
        """
        if not selected_items:
            return {'status': 'no_action', 'message': '선택된 항목이 없습니다.'}

        # 진단 재실행으로 최신 데이터 확보
        diagnosis_result = self.run_diagnosis()
        if diagnosis_result['status'] != 'success' or not diagnosis_result.get('not_kms_encrypted_trails'):
            return {'status': 'no_action', 'message': 'CloudTrail 암호화 조치가 필요한 항목이 없습니다.'}

        not_kms_encrypted_trails = diagnosis_result['not_kms_encrypted_trails']
        cloudtrail = self.session.client('cloudtrail')
        kms = self.session.client('kms')
        results = []
        
        print("[FIX] 4.5 CloudTrail SSE-KMS 암호화 조치를 시작합니다.")

        try:
            account_id = self.session.client('sts').get_caller_identity()['Account']
            region = boto3.session.Session().region_name
            alias_name = "alias/cloudtrail-autokey"
            key_arn = None

            # 1. 먼저 기존 alias 존재 여부 확인
            existing_aliases = kms.list_aliases()['Aliases']
            alias_dict = {a['AliasName']: a['TargetKeyId'] for a in existing_aliases if 'AliasName' in a and 'TargetKeyId' in a}

            if alias_name in alias_dict:
                print(f"[INFO] KMS 별칭 '{alias_name}'이 이미 존재합니다.")
                key_id = alias_dict[alias_name]
                key_arn = f"arn:aws:kms:{region}:{account_id}:key/{key_id}"
                print(f"[INFO] 기존 키 ARN 사용: {key_arn}")
            else:
                # 새 KMS 키 생성
                print(f"[INFO] 별칭 '{alias_name}'로 새 KMS 키를 생성합니다.")
                response = kms.create_key(
                    Description='CloudTrail 암호화를 위한 자동 생성 KMS 키',
                    KeyUsage='ENCRYPT_DECRYPT',
                    Origin='AWS_KMS'
                )
                key_id = response['KeyMetadata']['KeyId']
                key_arn = f"arn:aws:kms:{region}:{account_id}:key/{key_id}"

                policy = {
                    "Version": "2012-10-17",
                    "Id": "cloudtrail-access",
                    "Statement": [
                        {
                            "Sid": "Allow CloudTrail",
                            "Effect": "Allow",
                            "Principal": { "Service": "cloudtrail.amazonaws.com" },
                            "Action": ["kms:GenerateDataKey*", "kms:Decrypt"],
                            "Resource": "*"
                        },
                        {
                            "Sid": "Allow Admin",
                            "Effect": "Allow",
                            "Principal": { "AWS": f"arn:aws:iam::{account_id}:root" },
                            "Action": "kms:*",
                            "Resource": "*"
                        }
                    ]
                }

                kms.put_key_policy(
                    KeyId=key_id,
                    PolicyName='default',
                    Policy=json.dumps(policy)
                )

                kms.create_alias(AliasName=alias_name, TargetKeyId=key_id)
                print(f"[SUCCESS] 새 KMS 키 생성 완료")
                print(f"[INFO] 별칭: {alias_name}")
                print(f"[INFO] Key ARN: {key_arn}")

            # 3. 암수화 적용
            for trail_name in not_kms_encrypted_trails:
                # 선택된 항목인지 확인
                if any(trail_name in str(item) for item in selected_items.values() for item in item):
                    try:
                        cloudtrail.update_trail(Name=trail_name, KmsKeyId=key_arn)
                        print(f"     [SUCCESS] Trail '{trail_name}'에 KMS 암호화를 적용했습니다.")
                        results.append({
                            'status': 'success',
                            'resource': f"CloudTrail {trail_name}",
                            'action': f"KMS 암호화 적용",
                            'message': f"Trail '{trail_name}'에 KMS 암호화를 적용했습니다."
                        })
                    except ClientError as e:
                        print(f"     [ERROR] Trail '{trail_name}' 암호화 적용 실패: {e}")
                        results.append({
                            'status': 'error',
                            'resource': f"CloudTrail {trail_name}",
                            'error': str(e),
                            'message': f"Trail '{trail_name}' 암호화 적용 실패: {str(e)}"
                        })
                else:
                    print(f"     [INFO] Trail '{trail_name}' 암호화 적용을 건너뜁니다.")

            return {
                'status': 'success',
                'results': results,
                'message': f"{len(results)}개 항목에 대한 조치가 완료되었습니다."
            }

        except ClientError as e:
            print(f"[ERROR] KMS 키 생성 또는 설정 중 오류 발생: {e}")
            return {
                'status': 'error',
                'error_message': f"KMS 키 생성 또는 설정 중 오류 발생: {str(e)}"
            }

    def _get_manual_guide(self):
        """CloudTrail 암호화 수동 조치 가이드 반환"""
        return {
            'title': 'CloudTrail KMS 암호화 수동 설정 가이드',
            'description': 'CloudTrail KMS 암호화는 KMS 키 생성과 정책 설정이 필요하여 수동 조치가 필요합니다.',
            'steps': [
                {
                    'type': 'warning',
                    'title': '[주의] 복잡한 설정 과정',
                    'content': 'CloudTrail KMS 암호화는 KMS 키 생성, 정책 설정, CloudTrail 업데이트 등 여러 단계가 필요합니다.'
                },
                {
                    'type': 'step',
                    'title': '1. KMS 키 생성',
                    'content': 'AWS KMS 콘솔에서 CloudTrail 전용 KMS 키를 생성합니다.'
                },
                {
                    'type': 'step',
                    'title': '2. KMS 키 정책 설정',
                    'content': 'CloudTrail 서비스가 KMS 키를 사용할 수 있도록 키 정책을 설정합니다.'
                },
                {
                    'type': 'commands',
                    'title': 'KMS 키 정책 예시',
                    'content': [
                        '{',
                        '  "Version": "2012-10-17",',
                        '  "Statement": [',
                        '    {',
                        '      "Effect": "Allow",',
                        '      "Principal": {"Service": "cloudtrail.amazonaws.com"},',
                        '      "Action": ["kms:GenerateDataKey*", "kms:Decrypt"],',
                        '      "Resource": "*"',
                        '    }',
                        '  ]',
                        '}'
                    ]
                },
                {
                    'type': 'step',
                    'title': '3. CloudTrail 암호화 설정',
                    'content': 'CloudTrail 콘솔에서 각 Trail의 설정을 수정하여 생성한 KMS 키를 적용합니다.'
                },
                {
                    'type': 'step',
                    'title': '4. 암호화 적용 확인',
                    'content': 'CloudTrail 설정에서 KMS 키가 올바르게 적용되었는지 확인합니다.'
                },
                {
                    'type': 'info',
                    'title': '[참고] KMS 키 별칭 사용',
                    'content': 'KMS 키에 별칭(예: alias/cloudtrail-key)을 설정하면 관리가 더 쉬워집니다.'
                }
            ]
        }

    def get_fix_options(self, diagnosis_result):
        """자동 조치 옵션 반환"""
        if not diagnosis_result.get('not_kms_encrypted_trails'):
            return []
            
        not_kms_encrypted_trails = diagnosis_result.get('not_kms_encrypted_trails', [])
        
        return [{
            'id': 'apply_kms_encryption_to_trails',
            'title': 'CloudTrail KMS 암호화 적용',
            'description': 'CloudTrail에 KMS 암호화를 자동으로 적용합니다. (필요시 새 KMS 키 자동 생성)',
            'items': [
                {
                    'id': trail_name,
                    'name': f"CloudTrail {trail_name}",
                    'description': f"KMS 암호화 미적용 - 자동 적용 예정"
                }
                for trail_name in not_kms_encrypted_trails
            ]
        }]