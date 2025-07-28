"""
1.12 EKS 서비스 계정 체커
EKS 클러스터의 서비스 계정 보안을 점검합니다.
"""
import boto3
from botocore.exceptions import ClientError
from ..base_checker import BaseChecker

class EKSServiceAccountChecker(BaseChecker):
    """1.12 EKS 서비스 계정 체커"""
    
    @property
    def item_code(self):
        return "1.12"
    
    @property 
    def item_name(self):
        return "EKS 서비스 계정"
    
    def run_diagnosis(self):
        """진단 실행 - 원본 1.12 로직 그대로 구현"""
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
                    
                    # 원본 로직: 서비스 계정 토큰 자동 마운트 점검 (웹 환경에서는 직접 접근 불가)
                    # 따라서 수동 점검 필요함을 안내
                    network_failed_clusters.append({
                        'cluster_name': cluster_name,
                        'reason': 'Kubernetes API 접근 불가 (default SA 토큰 자동 마운트 점검 필요)',
                        'endpoint': cluster_info['cluster']['endpoint'],
                        'check_target': 'default 서비스 계정의 automountServiceAccountToken 설정'
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
                'recommendation': "EKS 클러스터의 'default' 서비스 계정 토큰 자동 마운트 설정을 수동으로 점검해야 합니다."
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
            return "[INFO] 1.12 점검할 EKS 클러스터가 없습니다."
        elif network_failed > 0:
            return f"[ⓘ MANUAL] 1.12 {network_failed}개 EKS 클러스터의 서비스 계정 토큰 설정을 수동 점검해야 합니다."
        else:
            return "[✓ COMPLIANT] 1.12 모든 EKS 클러스터의 서비스 계정 점검 완료."
    
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
                'description': '서비스 계정 토큰 설정 수동 점검 필요',
                'details': network_failed,
                'reason': 'default 서비스 계정의 automountServiceAccountToken 점검 필요'
            }
        
        return details
    
    def _get_fix_options(self, result):
        """자동 조치 옵션 반환"""
        # 원본: EKS 클러스터는 Kubernetes API 접근이 필요하므로 자동 조치 불가
        return None
    
    def _get_manual_guide(self, result):
        """수동 조치 가이드 반환 - 원본 1.12 로직"""
        if not result.get('has_issues'):
            return None
        
        network_failed = result.get('network_failed_clusters', [])
        if not network_failed:
            return None
        
        # 원본 수동 점검 가이드를 웹 UI로 변환
        guide_steps = [
            {
                'type': 'warning',
                'title': '[FIX] 1.12 EKS 서비스 계정 토큰 자동 마운트 점검',
                'content': "EKS 클러스터의 'default' 서비스 계정 토큰 자동 마운트 설정을 VPC 내부에서 점검해야 합니다."
            },
            {
                'type': 'info',
                'title': '점검 대상',
                'content': '사용자 네임스페이스의 default 서비스 계정에서 automountServiceAccountToken이 비활성화되어 있는지 확인합니다.'
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
                'title': '3. 네임스페이스별 서비스 계정 점검',
                'content': '각 사용자 네임스페이스의 default 서비스 계정 설정을 확인합니다.'
            }
        ]
        
        # 점검이 필요한 클러스터별 명령어 추가
        cli_commands = []
        for cluster in network_failed:
            cluster_name = cluster['cluster_name']
            cli_commands.extend([
                f"# 클러스터 '{cluster_name}' 서비스 계정 점검",
                f"aws eks update-kubeconfig --name {cluster_name}",
                "",
                "# 모든 네임스페이스의 default SA 확인",
                "kubectl get namespaces --no-headers | grep -v 'kube-' | awk '{print $1}' | while read ns; do",
                "  echo \"=== Namespace: $ns ===\"",
                "  kubectl get serviceaccount default -n $ns -o jsonpath='{.automountServiceAccountToken}' 2>/dev/null || echo 'true (default)'",
                "  echo",
                "done",
                "",
                "# 특정 네임스페이스 점검 예시",
                "kubectl get serviceaccount default -n default -o yaml | grep automountServiceAccountToken",
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
                'type': 'step',
                'title': '4. 토큰 자동 마운트 비활성화',
                'content': 'automountServiceAccountToken이 true인 default 서비스 계정을 false로 변경합니다.'
            },
            {
                'type': 'commands',
                'title': '서비스 계정 패치 명령어',
                'content': [
                    "# 특정 네임스페이스의 default SA 토큰 자동 마운트 비활성화",
                    "kubectl patch serviceaccount default -n <namespace> -p '{\"automountServiceAccountToken\": false}'",
                    "",
                    "# 모든 사용자 네임스페이스에 일괄 적용",
                    "kubectl get namespaces --no-headers | grep -v 'kube-' | awk '{print $1}' | while read ns; do",
                    "  kubectl patch serviceaccount default -n $ns -p '{\"automountServiceAccountToken\": false}'",
                    "  echo \"Patched default SA in namespace: $ns\"",
                    "done"
                ]
            }
        ])
        
        return {
            'title': '1.12 EKS 서비스 계정 수동 점검 가이드',
            'description': '원본 팀원이 작성한 수동 점검 절차를 따라 EKS 서비스 계정 보안을 강화하세요.',
            'steps': guide_steps
        }
    
    def execute_fix(self, selected_items):
        """자동 조치 실행"""
        # 원본: EKS는 Kubernetes API 접근이 필요하므로 자동 조치 불가
        return [{
            'item': 'manual_eks_sa_check',
            'status': 'info',
            'message': '[FIX] 1.12 EKS 서비스 계정은 VPC 내부에서 수동 점검이 필요합니다.'
        }, {
            'item': 'sa_token_check',
            'status': 'info',
            'message': 'default 서비스 계정의 automountServiceAccountToken 설정을 확인하세요.'
        }, {
            'item': 'security_recommendation',
            'status': 'info',
            'message': '보안을 위해 사용자 네임스페이스의 default SA 토큰 자동 마운트를 비활성화하는 것을 권장합니다.'
        }]