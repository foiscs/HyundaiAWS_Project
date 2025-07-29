"""
[3.9] EKS Pod 보안 정책 설정 체커
원본: SHIELDUS-AWS-CHECKER/virtual_resources/3_9_eks_pod_security_policy.py
"""

import boto3
from botocore.exceptions import ClientError
from app.checkers.base_checker import BaseChecker


class EksPodSecurityPolicyChecker(BaseChecker):
    def __init__(self, session=None):
        super().__init__(session)
        
    @property
    def item_code(self):
        return "3.9"
    
    @property 
    def item_name(self):
        return "EKS Pod 보안 정책 설정"
        
    def run_diagnosis(self):
        """
        [3.9] EKS Pod 보안 정책 설정
        - PSS가 'privileged'로 설정되었거나 미설정된 네임스페이스를 점검 (VPC 내부 접근 필요)
        """
        print("[INFO] 3.9 EKS Pod 보안 정책 설정 체크 중...")
        
        # EKS 클러스터 조회
        eks_clusters = self._get_eks_clusters()
        if not eks_clusters:
            print("[INFO] 점검할 EKS 클러스터가 없습니다.")
            return {
                'status': 'success',
                'has_issues': False,
                'risk_level': 'low',
                'message': '점검할 EKS 클러스터가 없습니다',
                'findings': [],
                'clusters': [],
                'summary': 'EKS 클러스터가 존재하지 않습니다.',
                'details': {'total_clusters': 0, 'manual_check_required': False}
            }

        print(f"[INFO] {len(eks_clusters)}개의 EKS 클러스터가 발견되었습니다.")
        print("[ⓘ MANUAL] EKS Pod Security Standards(PSS) 점검은 VPC 내부에서 kubectl 접근이 필요합니다.")
        print("  └─ 각 클러스터의 네임스페이스에서 pod-security.kubernetes.io/enforce 레이블을 확인해야 합니다.")
        
        # 모든 클러스터에 대해 수동 점검이 필요함을 표시
        findings = [{
            'cluster': cluster['name'],
            'endpoint': cluster['endpoint'],
            'status': cluster['status'],
            'issue': 'VPC 내부 접근 필요로 인한 수동 점검 필요'
        } for cluster in eks_clusters]

        has_issues = len(findings) > 0  # 수동 점검이 필요하므로 True
        risk_level = 'medium'  # 수동 점검 필요한 항목은 중간 위험도
        
        return {
            'status': 'success',
            'has_issues': has_issues,
            'risk_level': risk_level,
            'message': f"수동 점검이 필요한 EKS 클러스터 {len(eks_clusters)}개" if has_issues else "점검할 EKS 클러스터가 없습니다",
            'findings': findings,
            'clusters': eks_clusters,
            'summary': f"총 {len(eks_clusters)}개의 EKS 클러스터에 대한 Pod Security Standards 수동 점검이 필요합니다." if has_issues else "점검할 EKS 클러스터가 없습니다.",
            'details': {
                'total_clusters': len(eks_clusters),
                'manual_check_required': True,
                'requires_vpc_access': True,
                'cluster_details': eks_clusters
            }
        }

    def _get_eks_clusters(self):
        """EKS 클러스터 목록 조회"""
        try:
            eks = self.session.client('eks')
            cluster_names = eks.list_clusters()['clusters']
            
            clusters = []
            for cluster_name in cluster_names:
                try:
                    cluster_info = eks.describe_cluster(name=cluster_name)['cluster']
                    clusters.append({
                        'name': cluster_name,
                        'endpoint': cluster_info.get('endpoint', 'N/A'),
                        'status': cluster_info.get('status', 'UNKNOWN'),
                        'version': cluster_info.get('version', 'N/A'),
                        'platform_version': cluster_info.get('platformVersion', 'N/A')
                    })
                except ClientError as e:
                    print(f"[WARNING] 클러스터 '{cluster_name}' 정보 조회 실패: {e}")
            
            return clusters
            
        except ClientError as e:
            print(f"[ERROR] EKS 클러스터 목록 조회 실패: {e}")
            return []

    def execute_fix(self, selected_items):
        """
        [3.9] EKS Pod 보안 정책 설정 조치
        - VPC 내부 접근이 필요하므로 수동 가이드 제공
        """
        if not selected_items:
            return {'status': 'no_action', 'message': '선택된 항목이 없습니다.'}

        # 진단 재실행으로 최신 데이터 확보
        diagnosis_result = self.run_diagnosis()
        if diagnosis_result['status'] != 'success' or not diagnosis_result.get('clusters'):
            return {'status': 'no_action', 'message': '점검할 EKS 클러스터가 없습니다.'}

        print("[FIX] 3.9 Pod Security Standards(PSS) 레이블 조치를 시작합니다.")
        print("[ⓘ MANUAL] EKS 클러스터는 VPC 내부에서 kubectl로 접근해야 합니다.")

        return {
            'status': 'manual_required',
            'message': 'EKS Pod 보안 정책 설정은 VPC 내부 접근이 필요한 수동 조치입니다.',
            'manual_guide': self._get_manual_guide()
        }

    def _get_manual_guide(self):
        """수동 조치 가이드 반환"""
        return {
            'title': 'EKS Pod Security Standards 수동 설정 가이드',
            'description': 'EKS 클러스터의 Pod Security Standards를 설정하려면 VPC 내부에서 kubectl 접근이 필요합니다.',
            'steps': [
                {
                    'type': 'warning',
                    'title': '[주의] VPC 내부 접근 필요',
                    'content': 'EKS 클러스터 API 서버에 접근하려면 VPC 내부 환경(예: EC2, 베스천 호스트)에서 작업해야 합니다.'
                },
                {
                    'type': 'step',
                    'title': '1. kubectl 설정',
                    'content': '다음 명령어로 kubectl을 EKS 클러스터에 연결합니다.'
                },
                {
                    'type': 'commands',
                    'title': 'kubectl 설정 명령어',
                    'content': [
                        'aws eks update-kubeconfig --region <your-region> --name <cluster-name>',
                        'kubectl config current-context'
                    ]
                },
                {
                    'type': 'step',
                    'title': '2. 네임스페이스 점검',
                    'content': '현재 네임스페이스의 Pod Security Standards 설정을 확인합니다.'
                },
                {
                    'type': 'commands',
                    'title': '네임스페이스 점검 명령어',
                    'content': [
                        'kubectl get namespaces --show-labels',
                        'kubectl get ns -o jsonpath="{range .items[*]}{.metadata.name}{\"\\t\"}{.metadata.labels.pod-security\\.kubernetes\\.io/enforce}{\"\\n\"}{end}"'
                    ]
                },
                {
                    'type': 'step',
                    'title': '3. PSS 레이블 적용',
                    'content': 'privileged 모드이거나 미설정된 네임스페이스에 baseline 정책을 적용합니다.'
                },
                {
                    'type': 'commands',
                    'title': 'PSS 레이블 적용 명령어',
                    'content': [
                        'kubectl label namespace <namespace-name> pod-security.kubernetes.io/enforce=baseline',
                        'kubectl label namespace <namespace-name> pod-security.kubernetes.io/audit=baseline',
                        'kubectl label namespace <namespace-name> pod-security.kubernetes.io/warn=baseline'
                    ]
                },
                {
                    'type': 'info',
                    'title': '[참고] Pod Security Standards 레벨',
                    'content': 'privileged: 제한 없음, baseline: 최소 보안, restricted: 강화된 보안. 일반적으로 baseline 이상을 권장합니다.'
                }
            ]
        }

    def get_fix_options(self, diagnosis_result):
        """수동 조치 옵션 반환"""
        if not diagnosis_result.get('clusters'):
            return []
            
        clusters = diagnosis_result.get('clusters', [])
        
        return [{
            'id': 'manual_eks_pss_setup',
            'title': 'EKS Pod Security Standards 수동 설정',
            'description': 'VPC 내부에서 kubectl을 사용하여 Pod Security Standards를 설정합니다.',
            'is_manual': True,
            'items': [
                {
                    'id': cluster['name'],
                    'name': f"EKS 클러스터 {cluster['name']}",
                    'description': f"상태: {cluster['status']}, 버전: {cluster['version']} - VPC 내부 접근 필요"
                }
                for cluster in clusters
            ]
        }]