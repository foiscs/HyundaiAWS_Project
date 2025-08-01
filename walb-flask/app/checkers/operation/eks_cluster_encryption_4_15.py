"""
[4.15] EKS Cluster 암호화 설정 체커
원본: SHIELDUS-AWS-CHECKER/operation/4_15_eks_cluster_encryption.py
"""

import boto3
from botocore.exceptions import ClientError
from app.checkers.base_checker import BaseChecker


class EksClusterEncryptionChecker(BaseChecker):
    def __init__(self, session=None):
        super().__init__(session)
        
    @property
    def item_code(self):
        return "4.15"
    
    @property 
    def item_name(self):
        return "EKS Cluster 암호화 설정"
        
    def run_diagnosis(self):
        """
        [4.15] EKS Cluster 암호화 설정
        - EKS 클러스터의 시크릿(Secret) 암호화가 활성화되어 있는지 점검
        """
        print("[INFO] 4.15 EKS Cluster 암호화 설정 체크 중...")
        eks = self.session.client('eks')
        
        try:
            clusters = eks.list_clusters().get('clusters', [])
            if not clusters:
                print("[INFO] 4.15 점검할 EKS 클러스터가 없습니다.")
                return {
                    'status': 'success',
                    'has_issues': False,
                    'risk_level': 'low',
                    'message': '점검할 EKS 클러스터가 없습니다',
                    'findings': [],
                    'summary': '점검할 EKS 클러스터가 없습니다.',
                    'details': {
                        'total_clusters': 0,
                        'encrypted_clusters': 0,
                        'unencrypted_clusters': 0
                    }
                }

            unencrypted_clusters = []
            for name in clusters:
                try:
                    enc_config = eks.describe_cluster(name=name)['cluster'].get('encryptionConfig', [])
                    if not any('secrets' in cfg.get('resources', []) for cfg in enc_config):
                        unencrypted_clusters.append(name)
                except ClientError as e:
                    print(f"[ERROR] 클러스터 '{name}' 정보 확인 중 오류: {e}")

            if not unencrypted_clusters:
                print("[✓ COMPLIANT] 4.15 모든 EKS 클러스터의 시크릿 암호화가 활성화되어 있습니다.")
            else:
                print(f"[⚠ WARNING] 4.15 시크릿 암호화가 비활성화된 EKS 클러스터가 존재합니다 ({len(unencrypted_clusters)}개).")
                print(f"  ├─ 해당 클러스터: {', '.join(unencrypted_clusters)}")
        
            has_issues = len(unencrypted_clusters) > 0
            total_issues = len(unencrypted_clusters)
            risk_level = self.calculate_risk_level(total_issues)
            
            return {
                'status': 'success',
                'has_issues': has_issues,
                'risk_level': risk_level,
                'message': f"시크릿 암호화가 비활성화된 클러스터 {total_issues}개 발견" if has_issues else "모든 EKS 클러스터의 시크릿 암호화가 활성화되어 있습니다",
                'findings': unencrypted_clusters,
                'summary': f"시크릿 암호화 비활성화 클러스터 {len(unencrypted_clusters)}개" if has_issues else "모든 EKS 클러스터의 시크릿 암호화가 정상적으로 설정되어 있습니다.",
                'details': {
                    'total_clusters': len(clusters),
                    'encrypted_clusters': len(clusters) - len(unencrypted_clusters),
                    'unencrypted_clusters': len(unencrypted_clusters),
                    'unencrypted_clusters_list': unencrypted_clusters
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
        [4.15] EKS Cluster 암호화 설정 조치
        - 기존 클러스터에는 암호화 설정을 적용할 수 없음
        - 새 클러스터 생성 시 AWS 콘솔에서 encryptionConfig 포함하여 생성해야 함
        """
        if not selected_items:
            return {'status': 'no_action', 'message': '선택된 항목이 없습니다.'}

        # 진단 재실행으로 최신 데이터 확보
        diagnosis_result = self.run_diagnosis()
        if diagnosis_result['status'] != 'success' or not diagnosis_result.get('findings'):
            return {'status': 'no_action', 'message': 'EKS 클러스터 암호화 조치가 필요한 항목이 없습니다.'}

        unencrypted_clusters = diagnosis_result['findings']

        print("[FIX] 4.15 시크릿 암호화가 설정되지 않은 클러스터에 대한 수동 조치가 필요합니다.")
        print("      EKS는 클러스터 생성 시에만 시크릿 암호화를 설정할 수 있으므로 클러스터 재생성이 필요합니다")
        print("[GUIDE] 콘솔 기반 조치 방법:")
        print("  1. AWS Management Console → EKS → [클러스터 생성]")
        print("  2. '클러스터 이름, 버전, IAM 역할' 등 기본 정보 입력")
        print("  3. '시크릿 암호화' 항목에서 다음 설정 추가:")
        print("     - 암호화할 리소스: secrets")
        print("     - KMS 키: 기존 키 선택 또는 새 키 생성")
        print("  4. 나머지 설정 완료 후 클러스터 생성")
        print("  ※ 생성된 클러스터로 기존 리소스 마이그레이션 필요 (예: kubectl로 export/import)\n")

        return {
            'status': 'manual_required',
            'message': f"{len(unencrypted_clusters)}개 클러스터에 대한 수동 조치가 필요합니다.",
            'manual_guide': self._get_manual_guide(unencrypted_clusters)
        }

    def _get_manual_guide(self, unencrypted_clusters):
        """EKS 클러스터 암호화 수동 조치 가이드 반환"""
        return {
            'title': 'EKS 클러스터 시크릿 암호화 수동 조치 가이드',
            'description': 'EKS는 클러스터 생성 시에만 시크릿 암호화를 설정할 수 있으므로 클러스터 재생성이 필요합니다.',
            'steps': [
                {
                    'type': 'danger',
                    'title': '[중요] 클러스터 재생성 필요',
                    'content': 'EKS 클러스터의 시크릿 암호화는 생성 후 변경할 수 없으므로 새로운 클러스터 생성이 필요합니다.'
                },
                {
                    'type': 'step',
                    'title': '1. AWS Management Console 접속',
                    'content': 'AWS Management Console → EKS → [클러스터 생성] 선택'
                },
                {
                    'type': 'step',
                    'title': '2. 기본 정보 입력',
                    'content': '클러스터 이름, Kubernetes 버전, IAM 역할 등 기본 정보를 입력합니다.'
                },
                {
                    'type': 'step',
                    'title': '3. 시크릿 암호화 설정',
                    'content': '시크릿 암호화 항목에서 다음을 설정합니다:\n- 암호화할 리소스: secrets\n- KMS 키: 기존 키 선택 또는 새 키 생성'
                },
                {
                    'type': 'step',
                    'title': '4. 클러스터 생성 완료',
                    'content': '나머지 네트워킹, 로깅 등의 설정을 완료하고 클러스터를 생성합니다.'
                },
                {
                    'type': 'step',
                    'title': '5. 리소스 마이그레이션',
                    'content': 'kubectl을 사용하여 기존 클러스터의 리소스를 새 클러스터로 마이그레이션합니다.'
                },
                {
                    'type': 'commands',
                    'title': '마이그레이션 예시 명령어',
                    'content': [
                        'kubectl get all --all-namespaces -o yaml > backup.yaml',
                        'kubectl apply -f backup.yaml --context=new-cluster'
                    ]
                },
                {
                    'type': 'warning',
                    'title': '[주의] 서비스 중단',
                    'content': '클러스터 재생성 과정에서 서비스 중단이 발생할 수 있으므로 유지보수 시간을 계획하세요.'
                }
            ]
        }

    def get_fix_options(self, diagnosis_result):
        """자동 조치 옵션 반환 (수동 조치만 가능)"""
        if not diagnosis_result.get('findings'):
            return []
            
        unencrypted_clusters = diagnosis_result.get('findings', [])
        options = []
        
        # 시크릿 암호화가 비활성화된 클러스터 (수동 조치만)
        if unencrypted_clusters:
            options.append({
                'id': 'manual_cluster_encryption',
                'title': 'EKS 클러스터 시크릿 암호화 수동 설정',
                'description': f'{len(unencrypted_clusters)}개의 클러스터에 대한 재생성이 필요합니다.',
                'is_manual': True,
                'items': [
                    {
                        'id': cluster_name,
                        'name': f"클러스터 {cluster_name}",
                        'description': "시크릿 암호화 비활성화됨 - 클러스터 재생성 필요"
                    }
                    for cluster_name in unencrypted_clusters
                ]
            })
        
        return options

    @property
    def item_code(self):
        return "4.15"
    
    @property 
    def item_name(self):
        return "EKS Cluster 암호화 설정"