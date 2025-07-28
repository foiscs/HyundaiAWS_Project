import sys
import os
from kubernetes import client, config
from botocore.exceptions import ClientError
from urllib3.exceptions import MaxRetryError

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from modules.eks import _get_eks_clusters, _update_kubeconfig

K8S_API_TIMEOUT = 10

def check():
    """
    [1.13] EKS 익명 사용자 접근 통제
    - 'system:anonymous' 또는 'system:unauthenticated'에 불필요한 ClusterRoleBinding이 있는지 점검
    """
    print("[INFO] 1.13 EKS 익명 사용자 접근 통제 체크 중...")
    clusters = _get_eks_clusters()
    if not clusters:
        print("[INFO] 점검할 EKS 클러스터가 없습니다.")
        return []

    findings = []
    network_failed_clusters = []
    SAFE_BINDINGS = ["system:public-info-viewer", "system:discovery"]

    for cluster_name in clusters:
        if not _update_kubeconfig(cluster_name): continue
        
        try:
            config.load_kube_config()
            api = client.RbacAuthorizationV1Api()
            bindings = api.list_cluster_role_binding(_request_timeout=K8S_API_TIMEOUT).items
            
            for binding in bindings or []:
                if binding.role_ref.name in SAFE_BINDINGS: continue
                
                for subject in binding.subjects or []:
                    if subject.name in ["system:anonymous", "system:unauthenticated"]:
                        findings.append({'cluster': cluster_name, 'binding_name': binding.metadata.name, 'role_name': binding.role_ref.name})

        except (MaxRetryError, client.ApiException) as e:
            if "timed out" in str(e).lower() or isinstance(e, MaxRetryError):
                network_failed_clusters.append(cluster_name)
            else:
                print(f"[ERROR] 클러스터 '{cluster_name}'의 ClusterRoleBinding 조회 실패: {e}")
        except Exception as e:
            print(f"[ERROR] 클러스터 '{cluster_name}' 점검 중 예외 발생: {e}")

    if not findings and not network_failed_clusters:
        print("[✓ COMPLIANT] 1.13 익명 사용자에게 불필요한 권한이 부여되지 않았습니다.")
    if findings:
        print(f"[⚠ WARNING] 1.13 익명 사용자에게 불필요한 ClusterRoleBinding이 존재합니다 ({len(findings)}건).")
        for f in findings: print(f"  ├─ 클러스터 '{f['cluster']}'의 바인딩 '{f['binding_name']}'이(가) '{f['role_name']}' 역할을 부여함")
    if network_failed_clusters:
        print(f"[ⓘ MANUAL] 다음 클러스터는 네트워크 연결 실패({K8S_API_TIMEOUT}초 초과)로 점검이 불가능합니다:")
        for cluster in network_failed_clusters: print(f"  ├─ {cluster}")
    
    return findings

def fix(findings):
    if not findings: return

    print("[FIX] 1.13 익명 사용자 접근 권한 조치를 시작합니다. **이 작업은 매우 위험할 수 있습니다.**")
    from collections import defaultdict
    grouped_findings = defaultdict(list)
    for f in findings: grouped_findings[f['cluster']].append(f)

    for cluster_name, items in grouped_findings.items():
        if not _update_kubeconfig(cluster_name): continue
        
        print(f"  -> 클러스터 '{cluster_name}'의 다음 바인딩이 조치 대상입니다:")
        for item in items: print(f"     - {item['binding_name']}")
        
        if input(f"     위 바인딩들을 삭제하시겠습니까? (y/n): ").lower() != 'y': continue

        try:
            config.load_kube_config()
            api = client.RbacAuthorizationV1Api()
            for item in items:
                try:
                    api.delete_cluster_role_binding(name=item['binding_name'], _request_timeout=K8S_API_TIMEOUT)
                    print(f"     [SUCCESS] ClusterRoleBinding '{item['binding_name']}'을(를) 삭제했습니다.")
                except client.ApiException as e:
                    print(f"     [ERROR] 바인딩 '{item['binding_name']}' 삭제 실패: {e}")
        
        except Exception as e:
            print(f"     [ERROR] 클러스터 '{cluster_name}' 조치 중 예외 발생: {e}")

if __name__ == "__main__":
    findings_list = check()
    fix(findings_list)