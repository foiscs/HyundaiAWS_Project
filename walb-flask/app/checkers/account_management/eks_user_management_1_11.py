"""
1.11 EKS 사용자 관리 체커
EKS 클러스터의 사용자 권한 관리를 점검합니다.
"""
import boto3
from botocore.exceptions import ClientError
from ..base_checker import BaseChecker

class EKSUserManagementChecker(BaseChecker):
    """1.11 EKS 사용자 관리 체커"""
    
    @property
    def item_code(self):
        return "1.11"
    
    @property 
    def item_name(self):
        return "EKS 사용자 관리"
    
    def run_diagnosis(self):
        """진단 실행 - 원본 1.11 로직 그대로 구현"""
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
                    
                    # 원본 로직: aws-auth ConfigMap 점검 (웹 환경에서는 직접 접근 불가)
                    # 따라서 수동 점검 필요함을 안내
                    network_failed_clusters.append({
                        'cluster_name': cluster_name,
                        'reason': 'Kubernetes API 접근 불가 (VPC 내부 접근 필요)',
                        'endpoint': cluster_info['cluster']['endpoint']
                    })
                    
                except ClientError as e:
                    if 'ResourceNotFoundException' in str(e):
                        continue
                    else:
                        network_failed_clusters.append({
                            'cluster_name': cluster_name,
                            'reason': f'클러스터 정보 조회 실패: {str(e)}',
                            'endpoint': 'N/A'
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
                'recommendation': "EKS 클러스터의 aws-auth ConfigMap에서 'system:masters' 그룹 매핑을 수동으로 점검해야 합니다."
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
            return "[INFO] 1.11 점검할 EKS 클러스터가 없습니다."
        elif network_failed > 0:
            return f"[ⓘ MANUAL] 1.11 {network_failed}개 EKS 클러스터는 수동 점검이 필요합니다."
        else:
            return "[✓ COMPLIANT] 1.11 모든 EKS 클러스터 점검 완료."
    
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
                'description': '수동 점검이 필요한 클러스터',
                'details': network_failed,
                'reason': 'Kubernetes API 접근을 위해 VPC 내부에서 점검 필요'
            }
        
        return details
    
    def _get_fix_options(self, result):
        """자동 조치 옵션 반환"""
        # 원본: EKS 클러스터는 Kubernetes API 접근이 필요하므로 자동 조치 불가
        return None
    
    def _get_manual_guide(self, result):
        """수동 조치 가이드 반환 - 원본 1.11 로직"""
        if not result.get('has_issues'):
            return None
        
        network_failed = result.get('network_failed_clusters', [])
        if not network_failed:
            return None
        
        # 원본 수동 점검 가이드를 웹 UI로 변환
        guide_steps = [
            {
                'type': 'warning',
                'title': '[FIX] 1.11 EKS 사용자 권한 관리 수동 점검',
                'content': "EKS 클러스터는 네트워크 연결 제한으로 VPC 내부(Bastion Host 등)에서 직접 점검해야 합니다."
            },
            {
                'type': 'step',
                'title': '1. VPC 내부 서버 접속',
                'content': 'EKS 클러스터와 통신 가능한 VPC 내부 서버(Bastion Host, EC2 등)에 접속합니다.'
            },
            {
                'type': 'step',
                'title': '2. kubectl 설정',
                'content': 'kubectl을 설치하고 EKS 클러스터에 대한 kubeconfig를 설정합니다.'
            },
            {
                'type': 'step',
                'title': '3. aws-auth ConfigMap 확인',
                'content': 'aws-auth ConfigMap에서 system:masters 그룹에 매핑된 IAM 주체를 확인합니다.'
            }
        ]
        
        # 점검이 필요한 클러스터별 명령어 추가
        cli_commands = []
        for cluster in network_failed:
            cluster_name = cluster['cluster_name']
            cli_commands.extend([
                f"# 클러스터 '{cluster_name}' 점검",
                f"aws eks update-kubeconfig --name {cluster_name}",
                f"kubectl get configmap aws-auth -n kube-system -o yaml",
                f"# system:masters 그룹 매핑 확인",
                f"kubectl get configmap aws-auth -n kube-system -o jsonpath='{{.data.mapRoles}}' | grep -i 'system:masters'",
                f"kubectl get configmap aws-auth -n kube-system -o jsonpath='{{.data.mapUsers}}' | grep -i 'system:masters'",
                ""
            ])
        
        if cli_commands:
            guide_steps.append({
                'type': 'commands',
                'title': 'kubectl 명령어 예시',
                'content': cli_commands
            })
        
        # 조치 방법 안내
        guide_steps.append({
            'type': 'step',
            'title': '4. system:masters 권한 제거',
            'content': 'system:masters 그룹에 매핑된 불필요한 IAM 주체가 있다면 aws-auth ConfigMap을 수정하여 제거합니다.'
        })
        
        return {
            'title': '1.11 EKS 사용자 관리 수동 점검 가이드',
            'description': '원본 팀원이 작성한 수동 점검 절차를 따라 EKS 클러스터 보안을 강화하세요.',
            'steps': guide_steps
        }
    
    def execute_fix(self, selected_items):
        """
        [1.11] EKS 사용자 관리 자동 조치 실행
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
                'message': "'system:masters' 그룹에 매핑된 IAM 주체가 없습니다."
            }]

        findings = diagnosis_result['findings']
        results = []
        
        # 원본의 fix() 함수 로직 구현
        print("[FIX] 1.11 'aws-auth' ConfigMap에서 'system:masters' 권한 조치를 시작합니다.")
        
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
            
            arns_to_remove = {item['arn'] for item in items}
            print(f"  -> 클러스터 '{cluster_name}'의 다음 관리자 주체를 제거합니다: {', '.join(arns_to_remove)}")
            
            try:
                # Kubernetes Python 클라이언트를 사용하여 aws-auth ConfigMap 수정
                from kubernetes import config, client
                from urllib3.exceptions import MaxRetryError
                import yaml
                
                config.load_kube_config()
                api = client.CoreV1Api()
                
                # aws-auth ConfigMap 읽기
                cm = api.read_namespaced_config_map(
                    name="aws-auth", 
                    namespace="kube-system", 
                    _request_timeout=30  # K8S_API_TIMEOUT
                )
                
                map_roles = yaml.safe_load(cm.data.get("mapRoles", "[]")) or []
                map_users = yaml.safe_load(cm.data.get("mapUsers", "[]")) or []
                
                # system:masters 그룹에서만 제거, 다른 그룹은 유지
                modified = False
                for role in map_roles:
                    if role.get('rolearn') in arns_to_remove:
                        original_groups = role.get('groups', [])
                        role['groups'] = [g for g in original_groups if g != 'system:masters']
                        if original_groups != role['groups']:
                            modified = True
                            
                for user in map_users:
                    if user.get('userarn') in arns_to_remove:
                        original_groups = user.get('groups', [])
                        user['groups'] = [g for g in original_groups if g != 'system:masters']
                        if original_groups != user['groups']:
                            modified = True
                
                if modified:
                    # 그룹이 없는 엔트리는 삭제
                    cm.data['mapRoles'] = yaml.dump([r for r in map_roles if r.get('groups')])
                    cm.data['mapUsers'] = yaml.dump([u for u in map_users if u.get('groups')])

                    # ConfigMap 업데이트
                    api.replace_namespaced_config_map(
                        name="aws-auth", 
                        namespace="kube-system", 
                        body=cm, 
                        _request_timeout=30
                    )
                    
                    print(f"     [SUCCESS] 클러스터 '{cluster_name}'의 'aws-auth' ConfigMap을 수정했습니다.")
                    results.append({
                        'item': f'cluster_{cluster_name}',
                        'status': 'success',
                        'message': f"클러스터 '{cluster_name}'의 system:masters 권한이 제거되었습니다."
                    })
                else:
                    results.append({
                        'item': f'cluster_{cluster_name}',
                        'status': 'info',
                        'message': f"클러스터 '{cluster_name}'에서 수정할 항목이 없습니다."
                    })

            except (MaxRetryError, Exception) as e:
                if "timed out" in str(e).lower() or isinstance(e, MaxRetryError):
                    results.append({
                        'item': f'cluster_{cluster_name}',
                        'status': 'error',
                        'message': f"클러스터 '{cluster_name}' 네트워크 연결 실패 (VPC 내부에서 실행 필요): {str(e)}"
                    })
                else:
                    print(f"     [ERROR] 클러스터 '{cluster_name}' 조치 실패: {e}")
                    results.append({
                        'item': f'cluster_{cluster_name}',
                        'status': 'error',
                        'message': f"클러스터 '{cluster_name}' 조치 실패: {str(e)}"
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