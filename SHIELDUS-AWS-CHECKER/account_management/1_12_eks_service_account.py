import boto3
import subprocess
from kubernetes import client, config
from botocore.exceptions import ClientError
import os, sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

if project_root not in sys.path:
    sys.path.append(project_root)

from modules.eks import _get_eks_clusters, _update_kubeconfig

def check():
    """
    [1.12] EKS 서비스 어카운트 관리
    - 'default' 서비스 어카운트가 토큰을 자동으로 마운트하는지 점검
    """
    print("[INFO] 1.12 EKS 서비스 어카운트 관리 체크 중...")
    clusters = _get_eks_clusters()
    if not clusters:
        print("[INFO] 점검할 EKS 클러스터가 없습니다.")
        return []

    findings = []
    for cluster_name in clusters:
        if not _update_kubeconfig(cluster_name): continue
        
        try:
            config.load_kube_config()
            api = client.CoreV1Api()
            namespaces = [ns.metadata.name for ns in api.list_namespace().items]

            for ns in namespaces:
                sa = api.read_namespaced_service_account(name="default", namespace=ns)
                # automountServiceAccountToken이 명시적으로 false가 아니면 취약
                if sa.automount_service_account_token is not False:
                    findings.append({'cluster': cluster_name, 'namespace': ns})

        except client.ApiException as e:
            print(f"[ERROR] 클러스터 '{cluster_name}'의 서비스 어카운트 조회 실패: {e}")
        except Exception as e:
            print(f"[ERROR] 클러스터 '{cluster_name}' 점검 중 예외 발생: {e}")

    if not findings:
        print("[✓ COMPLIANT] 1.12 'default' 서비스 어카운트의 토큰 자동 마운트가 모두 비활성화되어 있습니다.")
    else:
        print(f"[⚠ WARNING] 1.12 'default' 서비스 어카운트 토큰 자동 마운트가 활성화된 네임스페이스가 있습니다 ({len(findings)}건).")
        for f in findings: print(f"  ├─ 클러스터 '{f['cluster']}', 네임스페이스 '{f['namespace']}'")
    
    return findings

def fix(findings):
    """
    [1.12] EKS 서비스 어카운트 관리 조치
    - 'default' 서비스 어카운트의 토큰 자동 마운트를 비활성화
    """
    if not findings: return

    print("[FIX] 1.12 'default' 서비스 어카운트 토큰 자동 마운트 비활성화 조치를 시작합니다.")
    # 클러스터별로 그룹화
    from collections import defaultdict
    grouped_findings = defaultdict(list)
    for f in findings:
        grouped_findings[f['cluster']].append(f['namespace'])

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
                    api.patch_namespaced_service_account(name="default", namespace=ns, body=patch_body)
                    print(f"     [SUCCESS] 네임스페이스 '{ns}'의 'default' SA를 패치했습니다.")
                except client.ApiException as e:
                    print(f"     [ERROR] 네임스페이스 '{ns}' 패치 실패: {e}")
        
        except Exception as e:
            print(f"     [ERROR] 클러스터 '{cluster_name}' 조치 중 예외 발생: {e}")

if __name__ == "__main__":
    findings_list = check()
    fix(findings_list)