"""
[4.13] 백업 사용 여부 체커
원본: SHIELDUS-AWS-CHECKER/operation/4_13_backup_usage.py
"""

import boto3
from botocore.exceptions import ClientError
from app.checkers.base_checker import BaseChecker


class BackupUsageChecker(BaseChecker):
    def __init__(self, session=None):
        super().__init__(session)
        
    @property
    def item_code(self):
        return "4.13"
    
    @property 
    def item_name(self):
        return "백업 사용 여부"
        
    def run_diagnosis(self):
        """
        [4.13] 백업 사용 여부
        - AWS Backup 플랜 존재 여부와 RDS 자동 백업 활성화 여부를 점검
        """
        print("[INFO] 4.13 백업 사용 여부 체크 중...")
        findings = {'no_backup_plan': True, 'rds_no_backup': [], 'rds_checked': False}
        
        try:
            if self.session.client('backup').list_backup_plans()['BackupPlansList']:
                findings['no_backup_plan'] = False
                print("[✓ COMPLIANT] 4.13 AWS Backup 플랜이 존재합니다.")
            else:
                print("[⚠ WARNING] 4.13 AWS Backup 플랜이 존재하지 않습니다. (EBS, EFS 등 점검 필요)")
        except ClientError as e:
            print(f"[ERROR] AWS Backup 점검 중 오류: {e}")
        
        try:
            rds_client = self.session.client('rds')
            dbs = rds_client.describe_db_instances()['DBInstances']
            if not dbs:
                print("[INFO] RDS 인스턴스가 존재하지 않습니다.")
            else:
                findings['rds_checked'] = True
                for inst in dbs:
                    if inst.get('BackupRetentionPeriod', 0) == 0:
                        findings['rds_no_backup'].append(inst['DBInstanceIdentifier'])
                if findings['rds_no_backup']:
                    print(f"[⚠ WARNING] 4.13 자동 백업이 비활성화된 RDS DB 인스턴스가 존재합니다: {findings['rds_no_backup']}")
                else:
                    print("[✓ COMPLIANT] 4.13 모든 RDS 인스턴스에 자동 백업이 활성화되어 있습니다.")
        except ClientError as e:
            print(f"[ERROR] RDS 점검 중 오류: {e}")

        has_issues = findings['no_backup_plan'] or bool(findings['rds_no_backup'])
        total_issues = (1 if findings['no_backup_plan'] else 0) + len(findings['rds_no_backup'])
        risk_level = self.calculate_risk_level(total_issues)
        
        return {
            'status': 'success',
            'has_issues': has_issues,
            'risk_level': risk_level,
            'message': f"백업 설정 문제 {total_issues}건 발견" if has_issues else "모든 백업 설정이 정상적으로 구성되어 있습니다",
            'findings': findings,
            'summary': f"AWS Backup 플랜 {'없음' if findings['no_backup_plan'] else '있음'}, RDS 자동 백업 비활성화 {len(findings['rds_no_backup'])}개" if has_issues else "모든 백업 설정이 안전합니다.",
            'details': {
                'backup_plan_exists': not findings['no_backup_plan'],
                'rds_checked': findings['rds_checked'],
                'rds_no_backup_count': len(findings['rds_no_backup']),
                'total_issues': total_issues
            }
        }

    def execute_fix(self, selected_items):
        """
        [4.13] 백업 사용 여부 조치
        - RDS 자동 백업 활성화, AWS Backup은 수동 안내
        """
        if not selected_items:
            return {'status': 'no_action', 'message': '선택된 항목이 없습니다.'}

        # 진단 재실행으로 최신 데이터 확보
        diagnosis_result = self.run_diagnosis()
        if diagnosis_result['status'] != 'success' or not diagnosis_result.get('findings'):
            return {'status': 'no_action', 'message': '백업 설정 조치가 필요한 항목이 없습니다.'}

        findings = diagnosis_result['findings']
        results = []

        if findings['no_backup_plan']:
            print("[FIX] 4.13 AWS Backup 플랜 생성은 백업 주기, 보관 정책 등 상세 설정이 필요하여 수동 조치를 권장합니다.")
            print("  └─ AWS Backup 콘솔에서 [백업 플랜 생성]을 통해 EBS, EFS, DynamoDB 등 중요 리소스에 대한 백업을 구성하세요.")

        if findings['rds_checked'] and findings['rds_no_backup']:
            rds = self.session.client('rds')
            print("[FIX] 4.13 RDS 자동 백업 설정 조치를 시작합니다.")
            
            for name in findings['rds_no_backup']:
                # 선택된 항목인지 확인
                if any(name in str(item) for item in selected_items.values() for item in item):
                    try:
                        # 웹 인터페이스에서는 기본값 사용 (7일 보존, 즉시 적용하지 않음)
                        retention_period = 7  # 기본값 7일
                        apply_immediately = False  # 다음 유지관리 시 적용
                        
                        rds.modify_db_instance(
                            DBInstanceIdentifier=name,
                            BackupRetentionPeriod=retention_period,
                            ApplyImmediately=apply_immediately
                        )
                        print(f"     [SUCCESS] '{name}' 자동 백업 설정 요청 완료 ({'다음 유지관리 시 적용됨'}).")
                        results.append({
                            'status': 'success',
                            'resource': name,
                            'action': 'RDS 자동 백업 활성화',
                            'message': f"RDS '{name}'의 자동 백업을 활성화했습니다 (보존기간: {retention_period}일)."
                        })
                    except ClientError as e:
                        print(f"     [ERROR] 수정 실패: {e}")
                        results.append({
                            'status': 'error',
                            'resource': name,
                            'error': str(e),
                            'message': f"RDS '{name}' 자동 백업 설정 실패: {str(e)}"
                        })

        # AWS Backup 플랜이 없으면 수동 가이드 포함
        if findings['no_backup_plan']:
            # 수동 조치 안내를 results에 추가
            results.append({
                'item': 'backup_plan_manual',
                'status': 'info',
                'message': f"RDS 자동 백업 {len([r for r in results if r['item'] != 'backup_plan_manual'])}건 완료. AWS Backup 플랜은 수동 설정이 필요합니다."
            })
            return results

        return results

    def _get_manual_guide(self, findings):
        """백업 설정 수동 조치 가이드 반환"""
        return {
            'title': 'AWS Backup 플랜 생성 수동 조치 가이드',
            'description': 'AWS Backup 플랜 생성은 백업 주기, 보관 정책 등 상세 설정이 필요하여 수동 조치를 권장합니다.',
            'steps': [
                {
                    'type': 'warning',
                    'title': '[주의] 백업 정책 사전 계획',
                    'content': 'AWS Backup 플랜 생성 시 백업 주기, 보관 정책, 리소스 선택 등을 신중하게 계획해야 합니다.'
                },
                {
                    'type': 'step',
                    'title': '1. AWS Backup 콘솔 접속',
                    'content': 'AWS Management Console에서 AWS Backup 서비스로 이동합니다.'
                },
                {
                    'type': 'step',
                    'title': '2. 백업 플랜 생성',
                    'content': '[백업 플랜 생성] 버튼을 클릭하여 새로운 백업 플랜을 생성합니다.'
                },
                {
                    'type': 'step',
                    'title': '3. 백업 규칙 설정',
                    'content': '백업 주기(일일, 주간, 월간), 백업 시간, 보관 기간 등을 설정합니다.'
                },
                {
                    'type': 'step',
                    'title': '4. 리소스 할당',
                    'content': 'EBS, EFS, DynamoDB, RDS 등 백업할 리소스를 태그나 리소스 ID로 지정합니다.'
                },
                {
                    'type': 'step',
                    'title': '5. IAM 역할 설정',
                    'content': 'AWS Backup이 리소스에 접근할 수 있도록 적절한 IAM 역할을 설정합니다.'
                },
                {
                    'type': 'info',
                    'title': '[참고] RDS 자동 백업',
                    'content': 'RDS 인스턴스의 자동 백업은 별도로 설정되며, 이는 AWS Backup과 독립적으로 작동합니다.'
                }
            ]
        }

    def get_fix_options(self, diagnosis_result):
        """자동 조치 옵션 반환"""
        if not diagnosis_result.get('findings'):
            return []
            
        findings = diagnosis_result.get('findings', {})
        options = []
        
        # RDS 자동 백업 비활성화된 인스턴스
        if findings.get('rds_no_backup'):
            options.append({
                'id': 'enable_rds_backup',
                'title': 'RDS 자동 백업 활성화',
                'description': '선택한 RDS 인스턴스의 자동 백업을 활성화합니다 (보존기간: 7일).',
                'items': [
                    {
                        'id': instance_id,
                        'name': f"RDS {instance_id}",
                        'description': "자동 백업 비활성화됨"
                    }
                    for instance_id in findings['rds_no_backup']
                ]
            })
        
        # AWS Backup 플랜 (수동 조치만)
        if findings.get('no_backup_plan'):
            options.append({
                'id': 'manual_backup_plan',
                'title': 'AWS Backup 플랜 수동 생성',
                'description': 'AWS Backup 플랜 생성을 위한 수동 조치가 필요합니다.',
                'is_manual': True,
                'items': [
                    {
                        'id': 'backup_plan_creation',
                        'name': 'AWS Backup 플랜',
                        'description': '백업 플랜이 존재하지 않음 - 수동 생성 필요'
                    }
                ]
            })
        
        return options

    @property
    def item_code(self):
        return "4.13"
    
    @property 
    def item_name(self):
        return "백업 사용 여부"