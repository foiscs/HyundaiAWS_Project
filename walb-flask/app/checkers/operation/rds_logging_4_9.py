"""
[4.9] RDS 로깅 설정 체커
원본: SHIELDUS-AWS-CHECKER/operation/4_9_rds_logging.py
"""

import boto3
from botocore.exceptions import ClientError
from app.checkers.base_checker import BaseChecker


class RdsLoggingChecker(BaseChecker):
    def __init__(self, session=None):
        super().__init__(session)
        
    @property
    def item_code(self):
        return "4.9"
    
    @property 
    def item_name(self):
        return "RDS 로깅 설정"
        
    def run_diagnosis(self):
        """
        [4.9] RDS 로깅 설정 점검 - PostgreSQL 전용
        - PostgreSQL 또는 Aurora PostgreSQL에서 'postgresql' 로그가 CloudWatch에 연동되어 있는지 확인
        """
        print("[INFO] 4.9 RDS PostgreSQL 로깅 설정 체크 중...")
        rds = self.session.client('rds')
        insufficient_logging_instances = {}

        try:
            insts = rds.describe_db_instances()['DBInstances']
            if not insts:
                print("[INFO] 4.9 확인할 RDS 인스턴스가 존재하지 않습니다.")
                return {
                    'status': 'success',
                    'has_issues': False,
                    'risk_level': 'low',
                    'message': '확인할 RDS 인스턴스가 존재하지 않습니다.',
                    'insufficient_instances': {},
                    'summary': 'RDS 인스턴스가 존재하지 않습니다.',
                    'details': {
                        'total_instances': 0,
                        'postgres_instances': 0,
                        'insufficient_instances_count': 0
                    }
                }

            postgres_instances = 0
            for inst in insts:
                db_id = inst['DBInstanceIdentifier']
                engine = inst['Engine']
                enabled_logs = inst.get('EnabledCloudwatchLogsExports', [])

                # PostgreSQL 계열만 필터링
                if 'postgres' in engine:
                    postgres_instances += 1
                    if 'postgresql' not in enabled_logs:
                        insufficient_logging_instances[db_id] = ['postgresql']

            if not insufficient_logging_instances:
                print("[✓ COMPLIANT] 4.9 모든 PostgreSQL RDS 인스턴스에 로그 내보내기가 설정되어 있습니다.")
                has_issues = False
                message = "모든 PostgreSQL RDS 인스턴스에 로그 내보내기가 설정되어 있습니다."
            else:
                print(f"[⚠ WARNING] 4.9 로그 미설정 PostgreSQL 인스턴스 발견 ({len(insufficient_logging_instances)}개).")
                for name in insufficient_logging_instances:
                    print(f"  ├─ {name} (필요 로그: postgresql)")
                has_issues = True
                message = f"로그 미설정 PostgreSQL 인스턴스 {len(insufficient_logging_instances)}개 발견"

            risk_level = self.calculate_risk_level(len(insufficient_logging_instances))
            
            return {
                'status': 'success',
                'has_issues': has_issues,
                'risk_level': risk_level,
                'message': message,
                'insufficient_instances': insufficient_logging_instances,
                'summary': f"로그 미설정 PostgreSQL 인스턴스 {len(insufficient_logging_instances)}개" if has_issues else "모든 PostgreSQL RDS 인스턴스에 로깅이 설정되어 있습니다.",
                'details': {
                    'total_instances': len(insts),
                    'postgres_instances': postgres_instances,
                    'insufficient_instances_count': len(insufficient_logging_instances)
                }
            }

        except ClientError as e:
            print(f"[ERROR] RDS 정보를 가져오는 중 오류 발생: {e}")
            return {
                'status': 'error',
                'error_message': f"RDS 정보를 가져오는 중 오류 발생: {str(e)}"
            }

    def execute_fix(self, selected_items):
        """
        [4.9] RDS 로깅 설정 조치 - PostgreSQL 전용
        """
        if not selected_items:
            return {'status': 'no_action', 'message': '선택된 항목이 없습니다.'}

        # 진단 재실행으로 최신 데이터 확보
        diagnosis_result = self.run_diagnosis()
        if diagnosis_result['status'] != 'success' or not diagnosis_result.get('insufficient_instances'):
            return {'status': 'no_action', 'message': 'RDS 로깅 조치가 필요한 항목이 없습니다.'}

        insufficient_logging_instances = diagnosis_result['insufficient_instances']
        rds = self.session.client('rds')
        results = []

        print("[FIX] 4.9 RDS PostgreSQL 로그 설정 조치 시작합니다.")
        
        for name in insufficient_logging_instances:
            # 선택된 항목인지 확인
            if any(name in str(item) for item in selected_items.values() for item in item):
                try:
                    current_logs = rds.describe_db_instances(DBInstanceIdentifier=name)['DBInstances'][0].get('EnabledCloudwatchLogsExports', [])
                    all_logs_to_enable = list(set(current_logs + ['postgresql']))

                    rds.modify_db_instance(
                        DBInstanceIdentifier=name,
                        CloudwatchLogsExportConfiguration={'EnableLogTypes': all_logs_to_enable},
                        ApplyImmediately=False
                    )
                    print(f"     [SUCCESS] '{name}' 로그 설정 수정 요청 완료 (재시작 없이 즉시 반영되거나, 유지관리 윈도우에 적용될 수 있음).")
                    results.append({
                        'status': 'success',
                        'resource': f"RDS Instance {name}",
                        'action': 'PostgreSQL 로그 내보내기 활성화',
                        'message': f"'{name}' 인스턴스의 PostgreSQL 로그 내보내기를 활성화했습니다."
                    })
                except ClientError as e:
                    print(f"     [ERROR] 인스턴스 수정 실패: {e}")
                    results.append({
                        'status': 'error',
                        'resource': f"RDS Instance {name}",
                        'error': str(e),
                        'message': f"'{name}' 인스턴스 로그 설정 수정 실패: {str(e)}"
                    })

        return {
            'status': 'success' if all(r['status'] == 'success' for r in results) else 'partial_success',
            'results': results,
            'message': f"{len(results)}개 RDS 인스턴스에 대한 로그 설정 조치가 완료되었습니다."
        }

    def get_fix_options(self, diagnosis_result):
        """자동 조치 옵션 반환"""
        if not diagnosis_result.get('insufficient_instances'):
            return []
            
        insufficient_instances = diagnosis_result.get('insufficient_instances', {})
        
        return [{
            'id': 'enable_postgresql_logging',
            'title': 'RDS PostgreSQL 로그 내보내기 활성화',
            'description': '선택한 PostgreSQL RDS 인스턴스에서 CloudWatch 로그 내보내기를 활성화합니다.',
            'items': [
                {
                    'id': instance_name,
                    'name': f"RDS 인스턴스 {instance_name}",
                    'description': "PostgreSQL 로그 내보내기 미설정"
                }
                for instance_name in insufficient_instances.keys()
            ]
        }]

    @property
    def item_code(self):
        return "4.9"
    
    @property
    def item_name(self):
        return "RDS 로깅 설정"