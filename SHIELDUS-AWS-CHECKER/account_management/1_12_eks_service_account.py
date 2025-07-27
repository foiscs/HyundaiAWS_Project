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
    [1.12] EKS 서비스 어카운트 관리
    - 'default' 서비스 어카운트가 토큰을 자동으로 마운트하는지 점검 (타임아웃 적용)
    """
    print("[INFO] 1.12 EKS 서비스 어카운트 관리 체크 중...")
    clusters = _get_eks_clusters()
    if not clusters:
        print("[INFO] 점검할 EKS 클러스터가 없습니다.")
        return []

    findings = []
    network_failed_clusters = []
    EXCLUDED_NAMESPACES = ['kube-system', 'kube-public', 'kube-node-lease']

    for cluster_name in clusters:
        if not _update_kubeconfig(cluster_name): continue
        
        try:
            config.load_kube_config()
            api = client.CoreV1Api()
            namespaces = api.list_namespace(_request_timeout=K8S_API_TIMEOUT).items

            for ns in namespaces:
                if ns.metadata.name in EXCLUDED_NAMESPACES: continue
                
                sa = api.read_namespaced_service_account(name="default", namespace=ns.metadata.name, _request_timeout=K8S_API_TIMEOUT)
                if sa.automount_service_account_token is not False:
                    findings.append({'cluster': cluster_name, 'namespace': ns.metadata.name})

        except (MaxRetryError, client.ApiException) as e:
            if "timed out" in str(e).lower() or isinstance(e, MaxRetryError):
                network_failed_clusters.append(cluster_name)
            else:
                print(f"[ERROR] 클러스터 '{cluster_name}'의 서비스 어카운트 조회 실패: {e}")
        except Exception as e:
            print(f"[ERROR] 클러스터 '{cluster_name}' 점검 중 예외 발생: {e}")

    if not findings and not network_failed_clusters:
        print("[✓ COMPLIANT] 1.12 사용자 네임스페이스의 'default' SA 토큰 자동 마운트가 모두 비활성화되어 있습니다.")
    if findings:
        print(f"[⚠ WARNING] 1.12 'default' SA 토큰 자동 마운트가 활성화된 네임스페이스가 있습니다 ({len(findings)}건).")
        for f in findings: print(f"  ├─ 클러스터 '{f['cluster']}', 네임스페이스 '{f['namespace']}'")
    if network_failed_clusters:
        print(f"[ⓘ MANUAL] 다음 클러스터는 네트워크 연결 실패({K8S_API_TIMEOUT}초 초과)로 점검이 불가능합니다:")
        for cluster in network_failed_clusters: print(f"  ├─ {cluster}")
    
    return findings

def fix(findings):
    if not findings: return

    print("[FIX] 1.12 'default' 서비스 어카운트 토큰 자동 마운트 비활성화 조치를 시작합니다.")
    from collections import defaultdict
    grouped_findings = defaultdict(list)
    for f in findings: grouped_findings[f['cluster']].append(f['namespace'])

    for cluster_name, namespaces in grouped_findings.items():
        if not _update_kubeconfig(cluster_name): continue
        
        if input(f"  -> 클러스터 '{cluster_name}'의 {len(namespaces)}개 네임스페이스에 조치를 적용하시겠습니까? (y/n): ").lower() != 'y':
            continue

        try:
            config.load_kube_config()
            api = client.CoreV1Api()
            patch_body = {"automountServiceAccountToken": False}

            for ns in namespaces:
                try:
                    api.patch_namespaced_service_account(name="default", namespace=ns, body=patch_body, _request_timeout=K8S_API_TIMEOUT)
                    print(f"     [SUCCESS] 네임스페이스 '{ns}'의 'default' SA를 패치했습니다.")
                except client.ApiException as e:
                    print(f"     [ERROR] 네임스페이스 '{ns}' 패치 실패: {e}")
        except Exception as e:
            print(f"     [ERROR] 클러스터 '{cluster_name}' 조치 중 예외 발생: {e}")

if __name__ == "__main__":
    findings_list = check()
    fix(findings_list)