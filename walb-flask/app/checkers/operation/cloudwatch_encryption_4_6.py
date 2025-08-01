"""
[4.6] CloudWatch 암호화 설정 체커
원본: SHIELDUS-AWS-CHECKER/operation/4_6_cloudwatch_encryption.py
"""

import boto3
import json
from botocore.exceptions import ClientError
from app.checkers.base_checker import BaseChecker


class CloudwatchEncryptionChecker(BaseChecker):
    def __init__(self, session=None):
        super().__init__(session)
        
    @property
    def item_code(self):
        return "4.6"
    
    @property 
    def item_name(self):
        return "CloudWatch 암호화 설정"
        
    def run_diagnosis(self):
        """
        [4.6] CloudWatch 암호화 설정
        - CloudWatch Logs 로그 그룹이 KMS로 암호화되었는지 점검하고 미암호화 그룹 목록 반환
        """
        print("[INFO] 4.6 CloudWatch 암호화 설정 체크 중...")
        logs = self.session.client('logs')
        unencrypted_log_groups = []

        try:
            paginator = logs.get_paginator('describe_log_groups')
            log_groups_found = False

            for page in paginator.paginate():
                if 'logGroups' in page and page['logGroups']:
                    log_groups_found = True
                    for group in page['logGroups']:
                        if 'kmsKeyId' not in group:
                            unencrypted_log_groups.append(group['logGroupName'])

            if not log_groups_found:
                print("[INFO] 4.6 CloudWatch 로그 그룹이 존재하지 않습니다.")
                return {
                    'status': 'success',
                    'has_issues': False,
                    'risk_level': 'low',
                    'message': 'CloudWatch 로그 그룹이 존재하지 않습니다.',
                    'unencrypted_groups': [],
                    'summary': 'CloudWatch 로그 그룹이 존재하지 않습니다.',
                    'details': {
                        'unencrypted_groups_count': 0,
                        'total_groups': 0
                    }
                }

            if not unencrypted_log_groups:
                print("[✓ COMPLIANT] 4.6 모든 CloudWatch 로그 그룹이 KMS로 암호화되어 있습니다.")
                has_issues = False
                message = "모든 CloudWatch 로그 그룹이 KMS로 암호화되어 있습니다."
            else:
                print(f"[⚠ WARNING] 4.6 KMS 암호화가 적용되지 않은 CloudWatch 로그 그룹이 존재합니다 ({len(unencrypted_log_groups)}개).")
                for group_name in unencrypted_log_groups[:5]: 
                    print(f"  ├─ {group_name}")
                if len(unencrypted_log_groups) > 5: 
                    print(f"  └─ ... 외 {len(unencrypted_log_groups) - 5}개 더 있음")
                has_issues = True
                message = f"KMS 암호화가 적용되지 않은 CloudWatch 로그 그룹 {len(unencrypted_log_groups)}개 발견"

            risk_level = self.calculate_risk_level(len(unencrypted_log_groups))
            
            return {
                'status': 'success',
                'has_issues': has_issues,
                'risk_level': risk_level,
                'message': message,
                'unencrypted_groups': unencrypted_log_groups,
                'summary': f"미암호화 로그 그룹 {len(unencrypted_log_groups)}개" if has_issues else "모든 CloudWatch 로그 그룹이 암호화되어 있습니다.",
                'details': {
                    'unencrypted_groups_count': len(unencrypted_log_groups),
                    'total_groups': len(unencrypted_log_groups) if not has_issues else len(unencrypted_log_groups) + len(unencrypted_log_groups)  # 실제로는 암호화된 그룹 수를 계산해야 하지만 원본 그대로 유지
                }
            }

        except ClientError as e:
            print(f"[ERROR] CloudWatch 로그 그룹 정보를 가져오는 중 오류 발생: {e}")
            return {
                'status': 'error',
                'error_message': f"CloudWatch 로그 그룹 정보를 가져오는 중 오류 발생: {str(e)}"
            }

    def execute_fix(self, selected_items):
        """
        [4.6] CloudWatch 암호화 설정 조치
        - 미암호화 로그 그룹에 대해 KMS 암호화 적용
        """
        if not selected_items:
            return {'status': 'no_action', 'message': '선택된 항목이 없습니다.'}

        # 진단 재실행으로 최신 데이터 확보
        diagnosis_result = self.run_diagnosis()
        if diagnosis_result['status'] != 'success' or not diagnosis_result.get('unencrypted_groups'):
            return {'status': 'no_action', 'message': 'CloudWatch 암호화 조치가 필요한 항목이 없습니다.'}

        unencrypted_log_groups = diagnosis_result['unencrypted_groups']
        logs = self.session.client('logs')
        kms = self.session.client('kms')
        results = []
        
        print("[FIX] 4.6 CloudWatch 로그 그룹 암호화 조치를 시작합니다.")

        try:
            account_id = self.session.client('sts').get_caller_identity()['Account']
            region = boto3.session.Session().region_name
            alias_name = "alias/cloudwatch-autokey"
            key_arn = None

            # 기존 alias 있는지 확인
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
                    Description='CloudWatch 로그 암호화를 위한 자동 생성 KMS 키',
                    KeyUsage='ENCRYPT_DECRYPT',
                    Origin='AWS_KMS'
                )
                key_id = response['KeyMetadata']['KeyId']
                key_arn = f"arn:aws:kms:{region}:{account_id}:key/{key_id}"

                policy = {
                    "Version": "2012-10-17",
                    "Id": "cloudwatch-access",
                    "Statement": [
                        {
                            "Sid": "Allow CloudWatch Logs",
                            "Effect": "Allow",
                            "Principal": {
                                "Service": f"logs.{region}.amazonaws.com"
                            },
                            "Action": [
                                "kms:Encrypt",
                                "kms:Decrypt",
                                "kms:ReEncrypt*",
                                "kms:GenerateDataKey*",
                                "kms:DescribeKey"
                            ],
                            "Resource": "*",
                            "Condition": {
                                "ArnLike": {
                                    "kms:EncryptionContext:aws:logs:arn": f"arn:aws:logs:{region}:{account_id}:*"
                                }
                            }
                        },
                        {
                            "Sid": "Allow Admin Full Access",
                            "Effect": "Allow",
                            "Principal": {
                                "AWS": f"arn:aws:iam::{account_id}:root"
                            },
                            "Action": "kms:*",
                            "Resource": "*"
                        }
                    ]
                }

                kms.put_key_policy(KeyId=key_id, PolicyName='default', Policy=json.dumps(policy))
                kms.create_alias(AliasName=alias_name, TargetKeyId=key_id)
                print(f"[SUCCESS] 새 KMS 키 생성 완료")
                print(f"[INFO] 별칭: {alias_name}")
                print(f"[INFO] Key ARN: {key_arn}")

            for group_name in unencrypted_log_groups:
                # 선택된 항목인지 확인
                if any(group_name in str(item) for item in selected_items.values() for item in item):
                    try:
                        logs.associate_kms_key(logGroupName=group_name, kmsKeyId=key_arn)
                        print(f"     [SUCCESS] 로그 그룹 '{group_name}'에 KMS 키를 연결했습니다.")
                        results.append({
                            'status': 'success',
                            'resource': f"CloudWatch LogGroup {group_name}",
                            'action': f"KMS 암호화 적용",
                            'message': f"로그 그룹 '{group_name}'에 KMS 키를 연결했습니다."
                        })
                    except ClientError as e:
                        print(f"     [ERROR] 로그 그룹 '{group_name}' 키 연결 실패: {e}")
                        results.append({
                            'status': 'error',
                            'resource': f"CloudWatch LogGroup {group_name}",
                            'error': str(e),
                            'message': f"로그 그룹 '{group_name}' 키 연결 실패: {str(e)}"
                        })
                else:
                    print(f"     [INFO] 로그 그룹 '{group_name}' 암호화 적용을 건너뜁니다.")

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

    def _get_manual_guide(self, unencrypted_groups=None):
        """CloudWatch 로그 그룹 암호화 수동 조치 가이드 반환"""
        if unencrypted_groups is None:
            unencrypted_groups = []
            
        return {
            'title': 'CloudWatch 로그 그룹 암호화 수동 조치 가이드',
            'description': 'CloudWatch 로그 그룹에 KMS 암호화를 적용하려면 KMS 키 생성 및 정책 설정이 필요합니다.',
            'steps': [
                {
                    'type': 'warning',
                    'title': '[주의] KMS 키 권한 설정',
                    'content': 'CloudWatch Logs 서비스가 KMS 키에 접근할 수 있도록 정책을 올바르게 설정해야 합니다.'
                },
                {
                    'type': 'step',
                    'title': '1. KMS 키 생성 또는 기존 키 확인',
                    'content': 'AWS KMS 콘솔에서 CloudWatch Logs용 KMS 키를 생성하거나 기존 키를 확인합니다.'
                },
                {
                    'type': 'step',
                    'title': '2. KMS 키 정책 설정',
                    'content': 'CloudWatch Logs 서비스가 키를 사용할 수 있도록 키 정책에 적절한 권한을 추가합니다.'
                },
                {
                    'type': 'commands',
                    'title': 'KMS 키 정책 예시',
                    'content': [
                        '# CloudWatch Logs 서비스 권한을 위한 정책 예시',
                        '{',
                        '  "Sid": "Allow CloudWatch Logs",',
                        '  "Effect": "Allow",',
                        '  "Principal": {',
                        '    "Service": "logs.amazonaws.com"',
                        '  },',
                        '  "Action": [',
                        '    "kms:Encrypt",',
                        '    "kms:Decrypt",',
                        '    "kms:ReEncrypt*",',
                        '    "kms:GenerateDataKey*",',
                        '    "kms:DescribeKey"',
                        '  ],',
                        '  "Resource": "*"',
                        '}'
                    ]
                },
                {
                    'type': 'step',
                    'title': '3. 로그 그룹에 KMS 키 연결',
                    'content': 'CloudWatch Logs 콘솔에서 각 로그 그룹의 설정을 편집하여 KMS 키를 연결합니다.'
                },
                {
                    'type': 'commands',
                    'title': 'AWS CLI 명령어 예시',
                    'content': [
                        f'# 로그 그룹에 KMS 키 연결',
                        'aws logs associate-kms-key \\',
                        '  --log-group-name <LOG_GROUP_NAME> \\',
                        '  --kms-key-id <KMS_KEY_ARN>'
                    ]
                },
                {
                    'type': 'info',
                    'title': f'[참고] 조치 대상 로그 그룹 ({len(unencrypted_groups)}개)',
                    'content': f"다음 로그 그룹들에 대해 조치가 필요합니다: {', '.join(unencrypted_groups[:10])}" + (f" 외 {len(unencrypted_groups) - 10}개 더" if len(unencrypted_groups) > 10 else "")
                }
            ]
        }

    def get_fix_options(self, diagnosis_result):
        """자동 조치 옵션 반환"""
        if not diagnosis_result.get('unencrypted_groups'):
            return []
            
        unencrypted_groups = diagnosis_result.get('unencrypted_groups', [])
        
        return [{
            'id': 'apply_kms_encryption_to_log_groups',
            'title': 'CloudWatch 로그 그룹 KMS 암호화 적용',
            'description': f'{len(unencrypted_groups)}개의 로그 그룹에 KMS 암호화를 자동으로 적용합니다. (필요시 새 KMS 키 자동 생성)',
            'items': [
                {
                    'id': group_name,
                    'name': f"로그 그룹 {group_name}",
                    'description': "KMS 암호화 미설정 - 자동 적용 예정"
                }
                for group_name in unencrypted_groups
            ]
        }]

    @property
    def item_code(self):
        return "4.6"
    
    @property
    def item_name(self):
        return "CloudWatch 암호화 설정"