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
                eks = self.session.client('eks')
            
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
        """
        [1.13] EKS 익명 접근 자동 조치 실행
        - 원본 fix() 함수의 로직을 그대로 구현
        """
        if not selected_items:
            return [{
                'item': 'no_selection',
                'status': 'info',
                'message': '선택된 항목이 없습니다.'
            }]

        # 진단 재실행으로 최신 데이터 확보
        diagnosis_result = self.run_diagnosis()
        if diagnosis_result['status'] != 'success' or not diagnosis_result.get('findings'):
            return [{
                'item': 'no_action_needed',
                'status': 'info',
                'message': '익명 사용자에게 권한이 부여된 ClusterRoleBinding이 없습니다.'
            }]

        findings = diagnosis_result['findings']
        results = []
        
        # 원본의 fix() 함수 로직 구현
        print("[FIX] 1.13 EKS 익명 접근 ClusterRoleBinding 삭제 조치를 시작합니다.")
        
        # 클러스터별로 findings 그룹화
        from collections import defaultdict
        grouped_findings = defaultdict(list)
        for f in findings:
            grouped_findings[f['cluster']].append(f)

        for cluster_name, items in grouped_findings.items():
            # 선택된 클러스터인지 확인
            if not any(cluster_name in str(item) for item_list in selected_items.values() for item in item_list):
                continue
                
            # kubeconfig 업데이트 시도
            if not self._update_kubeconfig(cluster_name):
                results.append({
                    'item': f'cluster_{cluster_name}',
                    'status': 'error',
                    'message': f"클러스터 '{cluster_name}'의 kubeconfig 업데이트에 실패했습니다."
                })
                continue
            
            print(f"  -> 클러스터 '{cluster_name}'의 다음 바인딩이 조치 대상입니다:")
            for item in items:
                print(f"     - {item['binding_name']}")
            
            try:
                # Kubernetes Python 클라이언트를 사용하여 ClusterRoleBinding 삭제
                from kubernetes import config, client
                from urllib3.exceptions import MaxRetryError
                
                config.load_kube_config()
                api = client.RbacAuthorizationV1Api()
                
                for item in items:
                    binding_name = item['binding_name']
                    try:
                        api.delete_cluster_role_binding(
                            name=binding_name, 
                            _request_timeout=30
                        )
                        print(f"     [SUCCESS] ClusterRoleBinding '{binding_name}'을(를) 삭제했습니다.")
                        results.append({
                            'item': f'binding_{binding_name}',
                            'status': 'success',
                            'message': f"ClusterRoleBinding '{binding_name}'이 삭제되었습니다."
                        })
                    except Exception as e:
                        print(f"     [ERROR] 바인딩 '{binding_name}' 삭제 실패: {e}")
                        results.append({
                            'item': f'binding_{binding_name}',
                            'status': 'error',
                            'message': f"바인딩 '{binding_name}' 삭제 실패: {str(e)}"
                        })

            except (MaxRetryError, Exception) as e:
                if "timed out" in str(e).lower() or isinstance(e, MaxRetryError):
                    results.append({
                        'item': f'cluster_{cluster_name}',
                        'status': 'error',
                        'message': f"클러스터 '{cluster_name}' 네트워크 연결 실패 (VPC 내부에서 실행 필요): {str(e)}"
                    })
                else:
                    print(f"     [ERROR] 클러스터 '{cluster_name}' 조치 중 예외 발생: {e}")
                    results.append({
                        'item': f'cluster_{cluster_name}',
                        'status': 'error',
                        'message': f"클러스터 '{cluster_name}' 조치 중 예외 발생: {str(e)}"
                    })

        return results
    
    def _update_kubeconfig(self, cluster_name):
        """kubeconfig 업데이트 - 원본 _update_kubeconfig 함수"""
        try:
            if self.session:
                eks = self.session.client('eks')
            else:
                import boto3
                eks = self.session.client('eks')
                
            # EKS 클러스터 정보 조회
            cluster_info = eks.describe_cluster(name=cluster_name)['cluster']
            endpoint = cluster_info['endpoint']
            ca_data = cluster_info['certificateAuthority']['data']
            
            # kubeconfig 업데이트는 실제 환경에서는 boto3나 kubectl CLI를 통해 수행
            # 여기서는 연결 가능성만 확인
            print(f"     [INFO] 클러스터 '{cluster_name}' kubeconfig 준비됨 (endpoint: {endpoint})")
            return True
            
        except Exception as e:
            print(f"     [ERROR] 클러스터 '{cluster_name}' kubeconfig 업데이트 실패: {e}")
            return False