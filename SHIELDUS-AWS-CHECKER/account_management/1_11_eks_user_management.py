import sys
import os
import yaml
from kubernetes import client, config
from botocore.exceptions import ClientError
from urllib3.exceptions import MaxRetryError

# 프로젝트 루트 디렉터리를 sys.path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from modules.eks import _get_eks_clusters, _update_kubeconfig

K8S_API_TIMEOUT = 10  # API 호출 타임아웃 (초)

def check():
    """
    [1.11] EKS 사용자 권한 관리
    - 'aws-auth' ConfigMap에서 'system:masters' 그룹 매핑을 점검 (타임아웃 적용)
    """
    print("[INFO] 1.11 EKS 사용자 권한 관리 체크 중...")
    clusters = _get_eks_clusters()
    if not clusters:
        print("[INFO] 점검할 EKS 클러스터가 없습니다.")
        return []

    findings = []
    network_failed_clusters = []

    for cluster_name in clusters:
        if not _update_kubeconfig(cluster_name):
            continue
        
        try:
            config.load_kube_config()
            api = client.CoreV1Api()
            cm = api.read_namespaced_config_map(
                name="aws-auth", 
                namespace="kube-system", 
                _request_timeout=K8S_API_TIMEOUT
            )
            
            map_roles = yaml.safe_load(cm.data.get("mapRoles", "[]")) or []
            map_users = yaml.safe_load(cm.data.get("mapUsers", "[]")) or []
            
            for role in map_roles:
                if "system:masters" in role.get("groups", []):
                    findings.append({'cluster': cluster_name, 'type': 'role', 'arn': role.get('rolearn', 'N/A')})
            for user in map_users:
                 if "system:masters" in user.get("groups", []):
                    findings.append({'cluster': cluster_name, 'type': 'user', 'arn': user.get('userarn', 'N/A')})

        except (MaxRetryError, client.ApiException) as e:
            if "timed out" in str(e).lower() or isinstance(e, MaxRetryError):
                network_failed_clusters.append(cluster_name)
            elif isinstance(e, client.ApiException) and e.status == 404:
                print(f"[INFO] 클러스터 '{cluster_name}'에 'aws-auth' ConfigMap이 없습니다.")
            else:
                print(f"[ERROR] 클러스터 '{cluster_name}'의 ConfigMap 조회 실패: {e}")
        except Exception as e:
            print(f"[ERROR] 클러스터 '{cluster_name}' 점검 중 예외 발생: {e}")

    # 결과 출력
    if not findings and not network_failed_clusters:
        print("[✓ COMPLIANT] 1.11 'system:masters' 그룹에 매핑된 IAM 주체가 없습니다.")
    if findings:
        print(f"[⚠ WARNING] 1.11 'system:masters' 그룹에 IAM 주체가 매핑되어 있습니다 ({len(findings)}건).")
        for f in findings: print(f"  ├─ 클러스터 '{f['cluster']}': {f['type']} '{f['arn']}'")
    if network_failed_clusters:
        print(f"[ⓘ MANUAL] 다음 클러스터는 네트워크 연결 실패({K8S_API_TIMEOUT}초 초과)로 점검이 불가능합니다:")
        for cluster in network_failed_clusters: print(f"  ├─ {cluster}")
        print("  └─ 🔧 이 클러스터들은 VPC 내부(Bastion Host 등)에서 스크립트를 직접 실행하여 점검해야 합니다.")
    
    return findings

def fix(findings):
    if not findings: return
    
    print("[FIX] 1.11 'aws-auth' ConfigMap에서 'system:masters' 권한 조치를 시작합니다.")
    from collections import defaultdict
    grouped_findings = defaultdict(list)
    for f in findings: grouped_findings[f['cluster']].append(f)

    for cluster_name, items in grouped_findings.items():
        if not _update_kubeconfig(cluster_name): continue
        
        arns_to_remove = {item['arn'] for item in items}
        print(f"  -> 클러스터 '{cluster_name}'의 다음 관리자 주체를 제거합니다: {', '.join(arns_to_remove)}")
        if input(f"     위 작업을 진행하시겠습니까? (y/n): ").lower() != 'y': continue

        try:
            config.load_kube_config()
            api = client.CoreV1Api()
            cm = api.read_namespaced_config_map(name="aws-auth", namespace="kube-system", _request_timeout=K8S_API_TIMEOUT)
            
            map_roles = yaml.safe_load(cm.data.get("mapRoles", "[]")) or []
            map_users = yaml.safe_load(cm.data.get("mapUsers", "[]")) or []
            
            # system:masters 그룹에서만 제거, 다른 그룹은 유지
            for role in map_roles:
                if role.get('rolearn') in arns_to_remove:
                    role['groups'] = [g for g in role.get('groups', []) if g != 'system:masters']
            for user in map_users:
                if user.get('userarn') in arns_to_remove:
                    user['groups'] = [g for g in user.get('groups', []) if g != 'system:masters']
            
            cm.data['mapRoles'] = yaml.dump([r for r in map_roles if r.get('groups')]) # 그룹이 없는 엔트리는 삭제
            cm.data['mapUsers'] = yaml.dump([u for u in map_users if u.get('groups')])

            api.replace_namespaced_config_map(name="aws-auth", namespace="kube-system", body=cm, _request_timeout=K8S_API_TIMEOUT)
            print(f"     [SUCCESS] 클러스터 '{cluster_name}'의 'aws-auth' ConfigMap을 수정했습니다.")

        except Exception as e:
            print(f"     [ERROR] 클러스터 '{cluster_name}' 조치 실패: {e}")

if __name__ == "__main__":
    findings_list = check()
    fix(findings_list)