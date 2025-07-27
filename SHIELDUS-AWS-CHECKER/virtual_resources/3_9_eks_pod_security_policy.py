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
    [3.9] EKS Pod 보안 정책 설정
    - PSS가 'privileged'로 설정되었거나 미설정된 네임스페이스를 점검 (타임아웃 적용)
    """
    print("[INFO] 3.9 EKS Pod 보안 정책 설정 체크 중...")
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
                
                labels = ns.metadata.labels or {}
                enforce_level = labels.get('pod-security.kubernetes.io/enforce')
                
                if not enforce_level:
                    findings.append({'cluster': cluster_name, 'namespace': ns.metadata.name, 'issue': 'PSS 레이블 미설정'})
                elif enforce_level == 'privileged':
                    findings.append({'cluster': cluster_name, 'namespace': ns.metadata.name, 'issue': 'privileged 모드 사용'})

        except (MaxRetryError, client.ApiException) as e:
            if "timed out" in str(e).lower() or isinstance(e, MaxRetryError):
                network_failed_clusters.append(cluster_name)
            else:
                print(f"[ERROR] 클러스터 '{cluster_name}'의 네임스페이스 조회 실패: {e}")
        except Exception as e:
            print(f"[ERROR] 클러스터 '{cluster_name}' 점검 중 예외 발생: {e}")

    if not findings and not network_failed_clusters:
        print("[✓ COMPLIANT] 3.9 모든 네임스페이스에 적절한 Pod Security Standard가 적용되어 있습니다.")
    if findings:
        print(f"[⚠ WARNING] 3.9 Pod Security Standard가 미흡한 네임스페이스가 존재합니다 ({len(findings)}건).")
        for f in findings: print(f"  ├─ 클러스터 '{f['cluster']}', 네임스페이스 '{f['namespace']}': {f['issue']}")
    if network_failed_clusters:
        print(f"[ⓘ MANUAL] 다음 클러스터는 네트워크 연결 실패({K8S_API_TIMEOUT}초 초과)로 점검이 불가능합니다:")
        for cluster in network_failed_clusters: print(f"  ├─ {cluster}")
    
    return findings

def fix(findings):
    if not findings: return

    print("[FIX] 3.9 Pod Security Standards(PSS) 레이블 조치를 시작합니다.")
    from collections import defaultdict
    grouped_findings = defaultdict(list)
    for f in findings: grouped_findings[f['cluster']].append(f['namespace'])

    for cluster_name, namespaces in grouped_findings.items():
        if not _update_kubeconfig(cluster_name): continue
        
        print(f"  -> 클러스터 '{cluster_name}'의 다음 네임스페이스가 조치 대상입니다: {', '.join(namespaces)}")
        if input(f"     위 네임스페이스에 PSS 'baseline' enforce 모드를 적용하시겠습니까? (y/n): ").lower() != 'y':
            continue

        try:
            config.load_kube_config()
            api = client.CoreV1Api()
            patch_body = {"metadata": {"labels": {"pod-security.kubernetes.io/enforce": "baseline"}}}

            for ns_name in namespaces:
                try:
                    api.patch_namespace(name=ns_name, body=patch_body, _request_timeout=K8S_API_TIMEOUT)
                    print(f"     [SUCCESS] 네임스페이스 '{ns_name}'에 'baseline' 레이블을 적용했습니다.")
                except client.ApiException as e:
                    print(f"     [ERROR] 네임스페이스 '{ns_name}' 패치 실패: {e}")
        except Exception as e:
            print(f"     [ERROR] 클러스터 '{cluster_name}' 조치 중 예외 발생: {e}")

if __name__ == "__main__":
    findings_list = check()
    fix(findings_list)