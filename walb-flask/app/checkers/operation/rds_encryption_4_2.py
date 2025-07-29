"""
[4.2] RDS 암호화 설정 체커
원본: SHIELDUS-AWS-CHECKER/operation/4_2_rds_encryption.py
"""

import boto3
from botocore.exceptions import ClientError
from app.checkers.base_checker import BaseChecker


class RdsEncryptionChecker(BaseChecker):
    def __init__(self, session=None):
        super().__init__(session)
        
    @property
    def item_code(self):
        return "4.2"
    
    @property 
    def item_name(self):
        return "RDS 암호화 설정"
        
    def run_diagnosis(self):
        """
        [4.2] RDS 암호화 설정
        - 암호화되지 않은 RDS DB 인스턴스/클러스터를 점검하고 목록을 반환
        """
        print("[INFO] 4.2 RDS 암호화 설정 체크 중...")
        rds = self.session.client('rds')
        unencrypted_resources = []
        unencrypted_details = []
        total_resources = 0  # 전체 리소스 수 추적

        try:
            # DB 인스턴스 점검
            instances = rds.describe_db_instances()['DBInstances']
            for inst in instances:
                total_resources += 1
                if not inst.get('StorageEncrypted'):
                    resource_desc = f"인스턴스: {inst['DBInstanceIdentifier']}"
                    unencrypted_resources.append(resource_desc)
                    unencrypted_details.append({
                        'type': 'instance',
                        'identifier': inst['DBInstanceIdentifier'],
                        'engine': inst.get('Engine', 'unknown'),
                        'status': inst.get('DBInstanceStatus', 'unknown')
                    })

            # DB 클러스터 점검
            clusters = rds.describe_db_clusters()['DBClusters']
            for cluster in clusters:
                total_resources += 1
                if not cluster.get('StorageEncrypted'):
                    resource_desc = f"클러스터: {cluster['DBClusterIdentifier']}"
                    unencrypted_resources.append(resource_desc)
                    unencrypted_details.append({
                        'type': 'cluster',
                        'identifier': cluster['DBClusterIdentifier'],
                        'engine': cluster.get('Engine', 'unknown'),
                        'status': cluster.get('Status', 'unknown')
                    })

            # 출력 분기 처리
            if total_resources == 0:
                print("[✓ INFO] 4.2 점검할 RDS 리소스가 존재하지 않습니다.")
            elif not unencrypted_resources:
                print("[✓ COMPLIANT] 4.2 모든 RDS 리소스가 암호화되어 있습니다.")
            else:
                print(f"[⚠ WARNING] 4.2 스토리지 암호화가 비활성화된 RDS 리소스가 존재합니다 ({len(unencrypted_resources)}개).")
                for res in unencrypted_resources:
                    print(f"  ├─ {res}")

            has_issues = len(unencrypted_resources) > 0
            risk_level = self.calculate_risk_level(len(unencrypted_resources))
            
            return {
                'status': 'success',
                'has_issues': has_issues,
                'risk_level': risk_level,
                'message': f"암호화되지 않은 RDS 리소스 {len(unencrypted_resources)}개 발견" if has_issues else "모든 RDS 리소스가 암호화되어 있습니다" if total_resources > 0 else "점검할 RDS 리소스가 존재하지 않습니다",
                'unencrypted_resources': unencrypted_resources,
                'unencrypted_details': unencrypted_details,
                'summary': f"총 {len(unencrypted_resources)}개의 미암호화 RDS 리소스가 발견되었습니다." if has_issues else "모든 RDS 리소스가 안전하게 암호화되어 있습니다." if total_resources > 0 else "RDS 리소스가 존재하지 않습니다.",
                'details': {
                    'total_resources': total_resources,
                    'unencrypted_count': len(unencrypted_resources),
                    'instances_count': len([d for d in unencrypted_details if d['type'] == 'instance']),
                    'clusters_count': len([d for d in unencrypted_details if d['type'] == 'cluster'])
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
        [4.2] RDS 암호화 설정 조치
        - 자동 조치 불가, 수동 마이그레이션 절차 안내
        """
        if not selected_items:
            return {'status': 'no_action', 'message': '선택된 항목이 없습니다.'}

        # 진단 재실행으로 최신 데이터 확보
        diagnosis_result = self.run_diagnosis()
        if diagnosis_result['status'] != 'success' or not diagnosis_result.get('unencrypted_resources'):
            return {'status': 'no_action', 'message': 'RDS 암호화 조치가 필요한 항목이 없습니다.'}

        print("[FIX] 4.2 기존 RDS 리소스의 암호화는 직접 활성화할 수 없어 수동 조치가 필요합니다.")
        print("  └─ 아래의 일반적인 마이그레이션 절차를 따르세요.")
        print("  └─ 1. 암호화되지 않은 DB 인스턴스/클러스터의 최종 스냅샷을 생성합니다.")
        print("  └─ 2. 생성된 스냅샷을 '암호화' 옵션을 사용하여 복사합니다.")
        print("  └─ 3. 암호화된 스냅샷으로부터 새 DB 인스턴스/클러스터를 복원합니다.")
        print("  └─ 4. 애플리케이션의 DB 엔드포인트를 새로 생성한 리소스로 변경하고, 테스트 후 기존 리소스를 삭제합니다.")

        return {
            'status': 'manual_required',
            'message': 'RDS 암호화 설정은 수동 마이그레이션이 필요합니다.',
            'manual_guide': self._get_manual_guide()
        }

    def _get_manual_guide(self):
        """RDS 암호화 수동 조치 가이드 반환"""
        return {
            'title': 'RDS 암호화 수동 마이그레이션 가이드',
            'description': '기존 RDS 리소스는 직접 암호화할 수 없어 스냅샷을 통한 마이그레이션이 필요합니다.',
            'steps': [
                {
                    'type': 'warning',
                    'title': '[주의] 서비스 중단 주의',
                    'content': 'RDS 마이그레이션 과정에서 데이터베이스 서비스 중단이 발생할 수 있습니다.'
                },
                {
                    'type': 'step',
                    'title': '1. 최종 스냅샷 생성',
                    'content': '암호화되지 않은 DB 인스턴스/클러스터의 최종 스냅샷을 생성합니다.'
                },
                {
                    'type': 'step',
                    'title': '2. 암호화된 스냅샷 복사',
                    'content': '생성된 스냅샷을 "암호화" 옵션을 활성화하여 복사합니다.'
                },
                {
                    'type': 'step',
                    'title': '3. 새 암호화된 DB 복원',
                    'content': '암호화된 스냅샷으로부터 새 DB 인스턴스/클러스터를 복원합니다.'
                },
                {
                    'type': 'step',
                    'title': '4. 애플리케이션 엔드포인트 변경',
                    'content': '애플리케이션의 DB 엔드포인트를 새로 생성한 리소스로 변경합니다.'
                },
                {
                    'type': 'step',
                    'title': '5. 테스트 및 기존 리소스 삭제',
                    'content': '충분한 테스트 후 기존 암호화되지 않은 리소스를 삭제합니다.'
                },
                {
                    'type': 'info',
                    'title': '[참고] DB 엔진별 고려사항',
                    'content': 'MySQL, PostgreSQL, MariaDB 등 엔진별로 마이그레이션 절차에 차이가 있을 수 있습니다.'
                }
            ]
        }

    def get_fix_options(self, diagnosis_result):
        """수동 조치 옵션 반환"""
        if not diagnosis_result.get('unencrypted_resources'):
            return []
            
        unencrypted_details = diagnosis_result.get('unencrypted_details', [])
        
        return [{
            'id': 'manual_rds_encryption',
            'title': 'RDS 암호화 수동 마이그레이션',
            'description': 'RDS 리소스를 암호화하려면 스냅샷을 통한 수동 마이그레이션이 필요합니다.',
            'is_manual': True,
            'items': [
                {
                    'id': detail['identifier'],
                    'name': f"{detail['type'].title()} {detail['identifier']}",
                    'description': f"엔진: {detail['engine']}, 상태: {detail['status']} - 수동 마이그레이션 필요"
                }
                for detail in unencrypted_details
            ]
        }]