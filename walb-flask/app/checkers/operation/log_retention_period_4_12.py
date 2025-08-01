"""
[4.12] 로그 보존 기간 설정 체커
원본: SHIELDUS-AWS-CHECKER/operation/4_12_log_retention_period.py
"""

import boto3
from botocore.exceptions import ClientError
from app.checkers.base_checker import BaseChecker


class LogRetentionPeriodChecker(BaseChecker):
    def __init__(self, session=None):
        super().__init__(session)
        
    @property
    def item_code(self):
        return "4.12"
    
    @property 
    def item_name(self):
        return "로그 보존 기간 설정"
        
    def run_diagnosis(self):
        """
        [4.12] CloudWatch 로그 보관 기간 설정 점검
        - 주요 로그 그룹의 보관 기간이 1년(365일) 이상으로 설정되어 있는지 확인
        - 설정이 없거나 365일 미만이면 취약
        """
        print("[INFO] 4.12 주요 CloudWatch 로그 그룹의 보관 기간 점검 중...")
        
        if self.session:
            logs = self.session.client('logs')
        else:
            logs = self.session.client('logs')
            
        short_retention_groups = []

        # 주요 키워드 (가이드 기준)
        target_keywords = ['cloudtrail', 'vpc-flow-logs', 'vpc/flowlogs', 'rds', 's3', 'efs', 'ebs', 'fsx', 'dynamodb']

        try:
            paginator = logs.get_paginator('describe_log_groups')
            for page in paginator.paginate():
                for group in page['logGroups']:
                    name = group['logGroupName'].lower()
                    if any(keyword in name for keyword in target_keywords):
                        retention = group.get('retentionInDays')
                        if retention is None or retention < 365:
                            short_retention_groups.append({
                                'name': group['logGroupName'],
                                'days': retention if retention is not None else '무제한'
                            })

            if not short_retention_groups:
                print("[✓ COMPLIANT] 4.12 모든 주요 로그 그룹의 보관 기간이 1년 이상으로 설정되어 있습니다.")
                has_issues = False
                message = "모든 주요 로그 그룹의 보관 기간이 1년 이상으로 설정되어 있습니다."
            else:
                print(f"[⚠ WARNING] 4.12 보관 기간이 1년 미만이거나 설정되지 않은 주요 로그 그룹이 있습니다 ({len(short_retention_groups)}개).")
                for f in short_retention_groups:
                    print(f"  ├─ {f['name']} (보관 기간: {f['days']}일)")
                has_issues = True
                message = f"보관 기간이 1년 미만인 주요 로그 그룹 {len(short_retention_groups)}개 발견"

            risk_level = self.calculate_risk_level(len(short_retention_groups))
            
            return {
                'status': 'success',
                'has_issues': has_issues,
                'risk_level': risk_level,
                'message': message,
                'short_retention_groups': short_retention_groups,
                'summary': f"보관 기간 미흡 로그 그룹 {len(short_retention_groups)}개" if has_issues else "모든 주요 로그 그룹의 보관 기간이 적절합니다.",
                'details': {
                    'total_short_retention': len(short_retention_groups),
                    'groups_list': short_retention_groups
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
        [4.12] 로그 보관 기간 조치
        - 보관 기간이 짧거나 설정되지 않은 그룹의 보관 기간을 365일로 수정
        """
        if not selected_items:
            return {'status': 'no_action', 'message': '선택된 항목이 없습니다.'}

        # 진단 재실행으로 최신 데이터 확보
        diagnosis_result = self.run_diagnosis()
        if diagnosis_result['status'] != 'success' or not diagnosis_result.get('short_retention_groups'):
            return {'status': 'no_action', 'message': '로그 보존 기간 조치가 필요한 항목이 없습니다.'}

        short_retention_groups = diagnosis_result['short_retention_groups']
        
        if self.session:
            logs = self.session.client('logs')
        else:
            logs = self.session.client('logs')
            
        results = []
        
        print("[FIX] 4.12 로그 그룹 보관 기간 설정 조치를 시작합니다.")
        
        for group in short_retention_groups:
            group_name = group['name']
            # 선택된 항목인지 확인
            if any(group_name in str(item) for item in selected_items.values() for item in item):
                display_days = f"{group['days']}일" if isinstance(group['days'], int) else "무제한(설정되지 않음)"
                try:
                    logs.put_retention_policy(logGroupName=group_name, retentionInDays=365)
                    print(f"     [SUCCESS] '{group_name}'의 보존 기간을 365일로 설정했습니다.")
                    results.append({
                        'status': 'success',
                        'resource': group_name,
                        'action': '로그 보존 기간 365일로 설정',
                        'message': f"'{group_name}' (기존: {display_days})의 보존 기간을 365일로 설정했습니다."
                    })
                except ClientError as e:
                    print(f"     [ERROR] 설정 실패: {e}")
                    results.append({
                        'status': 'error',
                        'resource': group_name,
                        'error': str(e),
                        'message': f"'{group_name}' 보존 기간 설정 실패: {str(e)}"
                    })
            else:
                print(f"     [SKIP] 로그 그룹 '{group_name}'는 건너뜁니다.")
        
        success_count = sum(1 for r in results if r['status'] == 'success')
        
        return {
            'status': 'success' if success_count > 0 else 'partial_success',
            'results': results,
            'message': f"{success_count}개 로그 그룹의 보존 기간 설정이 완료되었습니다."
        }

    def _get_fix_options(self, diagnosis_result):
        """자동 조치 옵션 반환"""
        if not diagnosis_result.get('short_retention_groups'):
            return []
            
        short_retention_groups = diagnosis_result.get('short_retention_groups', [])
        
        return [{
            'id': 'set_log_retention',
            'title': '로그 보존 기간 365일로 설정',
            'description': '선택한 로그 그룹의 보존 기간을 365일로 설정합니다.',
            'items': [
                {
                    'id': group['name'],
                    'name': group['name'],
                    'description': f"현재 보존 기간: {group['days']}일" if isinstance(group['days'], int) else "현재 보존 기간: 무제한"
                }
                for group in short_retention_groups
            ]
        }]