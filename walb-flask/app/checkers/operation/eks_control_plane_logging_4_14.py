"""
[4.14] EKS Cluster 제어 플레인 로깅 설정 체커
원본: SHIELDUS-AWS-CHECKER/operation/4_14_eks_control_plane_logging.py
"""

import boto3
from botocore.exceptions import ClientError
from app.checkers.base_checker import BaseChecker


class EksControlPlaneLoggingChecker(BaseChecker):
    def __init__(self, session=None):
        super().__init__(session)
        
    @property
    def item_code(self):
        return "4.14"
    
    @property 
    def item_name(self):
        return "EKS Cluster 제어 플레인 로깅 설정"
        
    def run_diagnosis(self):
        """
        [4.14] EKS Cluster 제어 플레인 로깅 설정
        - 모든 EKS 클러스터에서 5개 로그(api, audit, authenticator, controllerManager, scheduler)가 활성화되어 있는지 점검
        """
        print("[INFO] 4.14 EKS Cluster 제어 플레인 로깅 설정 체크 중...")
        eks = self.session.client('eks')

        try:
            clusters = eks.list_clusters().get('clusters', [])
            if not clusters:
                print("[INFO] 4.14 점검할 EKS 클러스터가 없습니다.")
                return {
                    'status': 'success',
                    'has_issues': False,
                    'risk_level': 'low',
                    'message': '점검할 EKS 클러스터가 없습니다',
                    'findings': [],
                    'summary': '점검할 EKS 클러스터가 없습니다.',
                    'details': {
                        'total_clusters': 0,
                        'compliant_clusters': 0,
                        'non_compliant_clusters': 0
                    }
                }

            required_logs = {'api', 'audit', 'authenticator', 'controllerManager', 'scheduler'}
            non_compliant_clusters = []

            for name in clusters:
                try:
                    cluster_info = eks.describe_cluster(name=name)['cluster']
                    if cluster_info.get('status') != 'ACTIVE':
                        print(f"[SKIP] 클러스터 '{name}'는 ACTIVE 상태가 아니므로 점검 제외.")
                        continue

                    logging_config = cluster_info.get('logging', {}).get('clusterLogging', [])
                    enabled_logs = {t for log in logging_config if log.get('enabled') for t in log.get('types', [])}
                    missing = required_logs - enabled_logs

                    if missing:
                        non_compliant_clusters.append({
                            'name': name,
                            'logs': list(enabled_logs),
                            'missing': list(missing)
                        })

                except ClientError as e:
                    print(f"[ERROR] 클러스터 '{name}' 정보 확인 중 오류: {e}")

            if not non_compliant_clusters:
                print("[✓ COMPLIANT] 4.14 모든 EKS 클러스터의 제어 플레인 로그가 설정되어 있습니다.")
            else:
                print(f"[⚠ WARNING] 4.14 제어 플레인 로그가 누락된 클러스터가 있습니다 ({len(non_compliant_clusters)}개):")
                for c in non_compliant_clusters:
                    print(f"  ├─ {c['name']} (활성 로그: {c['logs'] or '없음'}) → 누락 로그: {c['missing']}")

            has_issues = len(non_compliant_clusters) > 0
            total_issues = len(non_compliant_clusters)
            risk_level = self.calculate_risk_level(total_issues)
            
            return {
                'status': 'success',
                'has_issues': has_issues,
                'risk_level': risk_level,
                'message': f"제어 플레인 로그가 누락된 클러스터 {total_issues}개 발견" if has_issues else "모든 EKS 클러스터의 제어 플레인 로그가 설정되어 있습니다",
                'findings': non_compliant_clusters,
                'summary': f"제어 플레인 로그 누락 클러스터 {len(non_compliant_clusters)}개" if has_issues else "모든 EKS 클러스터의 제어 플레인 로그가 정상적으로 설정되어 있습니다.",
                'details': {
                    'total_clusters': len(clusters),
                    'compliant_clusters': len(clusters) - len(non_compliant_clusters),
                    'non_compliant_clusters': len(non_compliant_clusters),
                    'required_logs': list(required_logs)
                }
            }

        except ClientError as e:
            print(f"[ERROR] EKS 클러스터 목록을 가져오는 중 오류 발생: {e}")
            return {
                'status': 'error',
                'error_message': f"EKS 클러스터 목록을 가져오는 중 오류 발생: {str(e)}"
            }

    def execute_fix(self, selected_items):
        """
        [4.14] EKS Cluster 제어 플레인 로깅 설정 조치
        - 비활성화된 로그가 있는 클러스터에 대해 모든 제어 플레인 로그(api, audit, authenticator, controllerManager, scheduler)를 활성화
        """
        if not selected_items:
            return {'status': 'no_action', 'message': '선택된 항목이 없습니다.'}

        # 진단 재실행으로 최신 데이터 확보
        diagnosis_result = self.run_diagnosis()
        if diagnosis_result['status'] != 'success' or not diagnosis_result.get('findings'):
            return {'status': 'no_action', 'message': 'EKS 제어 플레인 로깅 조치가 필요한 항목이 없습니다.'}

        non_compliant_clusters = diagnosis_result['findings']
        eks = self.session.client('eks')
        all_types = ['api', 'audit', 'authenticator', 'controllerManager', 'scheduler']
        print("[FIX] 4.14 EKS 제어 플레인 로깅 활성화 조치를 시작합니다.")

        results = []

        for cluster in non_compliant_clusters:
            name = cluster['name']
            current_logs = cluster['logs']
            missing_logs = cluster['missing']

            # 선택된 항목인지 확인
            if any(name in str(item) for item in selected_items.values() for item in item):
                print(f"  ─ 클러스터 '{name}': 누락 로그 → {missing_logs}")
                
                try:
                    eks.update_cluster_config(
                        name=name,
                        logging={'clusterLogging': [{'types': all_types, 'enabled': True}]}
                    )
                    print(f"     [SUCCESS] 클러스터 '{name}'의 모든 제어 플레인 로그 활성화를 요청했습니다.")
                    results.append({
                        'status': 'success',
                        'resource': name,
                        'action': 'EKS 제어 플레인 로그 활성화',
                        'message': f"클러스터 '{name}'의 모든 제어 플레인 로그 활성화를 요청했습니다."
                    })
                except ClientError as e:
                    print(f"     [ERROR] 클러스터 '{name}' 설정 업데이트 실패: {e}")
                    results.append({
                        'status': 'error',
                        'resource': name,
                        'error': str(e),
                        'message': f"클러스터 '{name}' 설정 업데이트 실패: {str(e)}"
                    })
            else:
                print(f"     [SKIPPED] '{name}' 조치를 건너뜁니다.")

        success_count = sum(1 for r in results if r['status'] == 'success')
        
        return {
            'status': 'success' if success_count > 0 else 'partial_success',
            'results': results,
            'message': f"{success_count}개 클러스터에 대한 제어 플레인 로그 활성화가 완료되었습니다."
        }

    def get_fix_options(self, diagnosis_result):
        """자동 조치 옵션 반환"""
        if not diagnosis_result.get('findings'):
            return []
            
        non_compliant_clusters = diagnosis_result.get('findings', [])
        options = []
        
        # 제어 플레인 로그가 누락된 클러스터
        if non_compliant_clusters:
            options.append({
                'id': 'enable_control_plane_logging',
                'title': 'EKS 제어 플레인 로깅 활성화',
                'description': '선택한 클러스터의 모든 제어 플레인 로그를 활성화합니다.',
                'items': [
                    {
                        'id': cluster['name'],
                        'name': f"클러스터 {cluster['name']}",
                        'description': f"누락 로그: {', '.join(cluster['missing'])}"
                    }
                    for cluster in non_compliant_clusters
                ]
            })
        
        return options

    @property
    def item_code(self):
        return "4.14"
    
    @property 
    def item_name(self):
        return "EKS Cluster 제어 플레인 로깅 설정"