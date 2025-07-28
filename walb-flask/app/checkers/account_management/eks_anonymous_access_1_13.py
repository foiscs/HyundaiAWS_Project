"""
1.13 EKS 익명 접근 체커
EKS 클러스터의 익명 접근을 점검합니다.
"""
import boto3
from botocore.exceptions import ClientError
from ..base_checker import BaseChecker

class EKSAnonymousAccessChecker(BaseChecker):
    """1.13 EKS 익명 접근 체커"""
    
    @property
    def item_code(self):
        return "1.13"
    
    @property 
    def item_name(self):
        return "EKS 익명 접근"
    
    def run_diagnosis(self):
        """진단 실행 - 원본 1.13 로직 그대로 구현"""
        try:
            if self.session:
                eks = self.session.client('eks')
            else:
                eks = boto3.client('eks')
            
            # EKS 클러스터 목록 조회
            clusters = []
            try:
                paginator = eks.get_paginator('list_clusters')
                for page in paginator.paginate():
                    clusters.extend(page['clusters'])
            except ClientError as e:
                return {
                    'status': 'error',
                    'error_message': f'EKS 클러스터 목록 조회 실패: {str(e)}'
                }
            
            if not clusters:
                return {
                    'status': 'success',
                    'has_issues': False,
                    'risk_level': 'low',
                    'total_clusters': 0,
                    'checked_clusters': 0,
                    'findings': [],
                    'network_failed_clusters': [],
                    'recommendation': '점검할 EKS 클러스터가 없습니다.'
                }
            
            findings = []
            network_failed_clusters = []
            checked_clusters = []
            
            # 각 클러스터에 대한 진단
            # 주의: 실제 Kubernetes API 접근은 네트워크 연결이 필요하므로 시뮬레이션
            for cluster_name in clusters:
                try:
                    # 클러스터 정보 조회
                    cluster_info = eks.describe_cluster(name=cluster_name)
                    cluster_status = cluster_info['cluster']['status']
                    
                    if cluster_status != 'ACTIVE':
                        continue
                        
                    checked_clusters.append(cluster_name)
                    
                    # 원본 로직: ClusterRoleBinding에서 익명 사용자 권한 점검 (웹 환경에서는 직접 접근 불가)
                    # 따라서 수동 점검 필요함을 안내
                    network_failed_clusters.append({
                        'cluster_name': cluster_name,
                        'reason': 'Kubernetes API 접근 불가 (익명 사용자 ClusterRoleBinding 점검 필요)',
                        'endpoint': cluster_info['cluster']['endpoint'],
                        'check_target': 'system:anonymous, system:unauthenticated 권한 점검'
                    })
                    
                except ClientError as e:
                    if 'ResourceNotFoundException' in str(e):
                        continue
                    else:
                        network_failed_clusters.append({
                            'cluster_name': cluster_name,
                            'reason': f'클러스터 정보 조회 실패: {str(e)}',
                            'endpoint': 'N/A',
                            'check_target': 'N/A'
                        })
            
            # 결과 분석
            has_issues = len(network_failed_clusters) > 0  # 수동 점검이 필요한 클러스터가 있으면 이슈로 간주
            risk_level = self.calculate_risk_level(len(network_failed_clusters))
            
            return {
                'status': 'success',
                'has_issues': has_issues,
                'risk_level': risk_level,
                'total_clusters': len(clusters),
                'checked_clusters': len(checked_clusters),
                'findings': findings,
                'network_failed_clusters': network_failed_clusters,
                'recommendation': "EKS 클러스터의 익명 사용자 접근 권한을 수동으로 점검해야 합니다."
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error_message': f'진단 수행 중 예상치 못한 오류가 발생했습니다: {str(e)}'
            }
    
    def _format_result_summary(self, result):
        """결과 요약 포맷팅"""
        total_clusters = result.get('total_clusters', 0)
        network_failed = len(result.get('network_failed_clusters', []))
        
        if total_clusters == 0:
            return "[INFO] 1.13 점검할 EKS 클러스터가 없습니다."
        elif network_failed > 0:
            return f"[ⓘ MANUAL] 1.13 {network_failed}개 EKS 클러스터의 익명 접근 권한을 수동 점검해야 합니다."
        else:
            return "[✓ COMPLIANT] 1.13 모든 EKS 클러스터의 익명 접근 점검 완료."
    
    def _format_result_details(self, result):
        """결과 상세 정보 포맷팅"""
        details = {
            'total_clusters': {
                'count': result.get('total_clusters', 0),
                'description': '전체 EKS 클러스터 수'
            },
            'checked_clusters': {
                'count': result.get('checked_clusters', 0),
                'description': '점검 가능한 클러스터 수'
            }
        }
        
        network_failed = result.get('network_failed_clusters', [])
        if network_failed:
            details['manual_check_required'] = {
                'count': len(network_failed),
                'clusters': [cluster['cluster_name'] for cluster in network_failed],
                'description': '익명 사용자 접근 권한 수동 점검 필요',
                'details': network_failed,
                'reason': 'system:anonymous, system:unauthenticated ClusterRoleBinding 점검 필요'
            }
        
        return details
    
    def _get_fix_options(self, result):
        """자동 조치 옵션 반환"""
        # 원본: EKS 클러스터는 Kubernetes API 접근이 필요하므로 자동 조치 불가
        return None
    
    def _get_manual_guide(self, result):
        """수동 조치 가이드 반환 - 원본 1.13 로직"""
        if not result.get('has_issues'):
            return None
        
        network_failed = result.get('network_failed_clusters', [])
        if not network_failed:
            return None
        
        # 원본 수동 점검 가이드를 웹 UI로 변환
        guide_steps = [
            {
                'type': 'warning',
                'title': '[FIX] 1.13 EKS 익명 사용자 접근 통제 점검',
                'content': "EKS 클러스터의 익명 사용자(system:anonymous, system:unauthenticated) 접근 권한을 VPC 내부에서 점검해야 합니다."
            },
            {
                'type': 'info',
                'title': '점검 대상',
                'content': 'ClusterRoleBinding에서 익명 사용자에게 불필요한 권한이 부여되지 않았는지 확인합니다.'
            },
            {
                'type': 'info',
                'title': '안전한 바인딩',
                'content': 'system:public-info-viewer, system:discovery는 일반적으로 안전한 바인딩입니다.'
            },
            {
                'type': 'step',
                'title': '1. VPC 내부 서버 접속',
                'content': 'EKS 클러스터와 통신 가능한 VPC 내부 서버에 접속합니다.'
            },
            {
                'type': 'step',
                'title': '2. kubectl 설정',
                'content': 'kubectl을 설치하고 EKS 클러스터에 대한 kubeconfig를 설정합니다.'
            },
            {
                'type': 'step',
                'title': '3. ClusterRoleBinding 점검',
                'content': '익명 사용자에게 부여된 ClusterRoleBinding을 확인합니다.'
            }
        ]
        
        # 점검이 필요한 클러스터별 명령어 추가
        cli_commands = []
        for cluster in network_failed:
            cluster_name = cluster['cluster_name']
            cli_commands.extend([
                f"# 클러스터 '{cluster_name}' 익명 접근 권한 점검",
                f"aws eks update-kubeconfig --name {cluster_name}",
                "",
                "# 모든 ClusterRoleBinding에서 익명 사용자 권한 확인",
                "kubectl get clusterrolebindings -o json | jq -r '.items[] | select(.subjects[]? | select(.name == \"system:anonymous\" or .name == \"system:unauthenticated\")) | \"\\(.metadata.name) -> \\(.roleRef.name)\"'",
                "",
                "# 상세 확인",
                "kubectl get clusterrolebindings -o yaml | grep -B5 -A5 'system:anonymous\\|system:unauthenticated'",
                "",
                "# 특정 바인딩 상세 정보",
                "kubectl describe clusterrolebinding <binding-name>",
                ""
            ])
        
        if cli_commands:
            guide_steps.append({
                'type': 'commands',
                'title': 'kubectl 점검 명령어',
                'content': cli_commands
            })
        
        # 조치 방법 안내
        guide_steps.extend([
            {
                'type': 'danger',
                'title': '⚠️ 주의사항',
                'content': '익명 사용자 권한 조치는 클러스터 접근성에 영향을 줄 수 있으므로 매우 신중하게 진행해야 합니다.'
            },
            {
                'type': 'step',
                'title': '4. 불필요한 바인딩 제거',
                'content': '안전하지 않은 ClusterRoleBinding을 확인 후 제거합니다. (system:public-info-viewer, system:discovery 제외)'
            },
            {
                'type': 'commands',
                'title': '조치 명령어 (신중히 사용)',
                'content': [
                    "# 특정 ClusterRoleBinding 삭제 (매우 위험할 수 있음)",
                    "kubectl delete clusterrolebinding <binding-name>",
                    "",
                    "# 삭제 전 백업",
                    "kubectl get clusterrolebinding <binding-name> -o yaml > backup-<binding-name>.yaml",
                    "",
                    "# 백업에서 복원 (필요시)",
                    "kubectl apply -f backup-<binding-name>.yaml"
                ]
            }
        ])
        
        return {
            'title': '1.13 EKS 익명 접근 수동 점검 가이드',
            'description': '원본 팀원이 작성한 수동 점검 절차를 따라 EKS 익명 접근 보안을 강화하세요.',
            'steps': guide_steps
        }
    
    def execute_fix(self, selected_items):
        """자동 조치 실행"""
        # 원본: EKS는 Kubernetes API 접근이 필요하므로 자동 조치 불가
        return [{
            'item': 'manual_eks_anonymous_check',
            'status': 'info',
            'message': '[FIX] 1.13 EKS 익명 접근은 VPC 내부에서 수동 점검이 필요합니다.'
        }, {
            'item': 'anonymous_access_check',
            'status': 'info',
            'message': 'system:anonymous, system:unauthenticated 사용자의 ClusterRoleBinding을 확인하세요.'
        }, {
            'item': 'security_warning',
            'status': 'warning',
            'message': '⚠️ 익명 사용자 권한 조치는 클러스터 접근성에 영향을 줄 수 있으므로 매우 신중하게 진행하세요.'
        }]