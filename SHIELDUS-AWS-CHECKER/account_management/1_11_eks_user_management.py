import sys
import os
import yaml
from kubernetes import client, config
from botocore.exceptions import ClientError

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

if project_root not in sys.path:
    sys.path.append(project_root)

from modules.eks import _get_eks_clusters, _update_kubeconfig

def check():
    """
    [1.11] EKS 사용자 권한 관리
    - 'aws-auth' ConfigMap에서 'system:masters' 그룹에 과도하게 많은 IAM 주체가 매핑되었는지 점검
    """
    print("[INFO] 1.11 EKS 사용자 권한 관리 체크 중...")
    clusters = _get_eks_clusters()
    if not clusters:
        print("[INFO] 점검할 EKS 클러스터가 없습니다.")
        return []

    findings = []
    for cluster_name in clusters:
        if not _update_kubeconfig(cluster_name):
            continue
        
        try:
            config.load_kube_config()
            api = client.CoreV1Api()
            cm = api.read_namespaced_config_map(name="aws-auth", namespace="kube-system")
            
            map_roles = yaml.safe_load(cm.data.get("mapRoles", "[]"))
            map_users = yaml.safe_load(cm.data.get("mapUsers", "[]"))
            
            for role in map_roles:
                if "system:masters" in role.get("groups", []):
                    findings.append({'cluster': cluster_name, 'type': 'role', 'arn': role['rolearn']})
            for user in map_users:
                 if "system:masters" in user.get("groups", []):
                    findings.append({'cluster': cluster_name, 'type': 'user', 'arn': user['userarn']})

        except client.ApiException as e:
            if e.status == 404:
                print(f"[INFO] 클러스터 '{cluster_name}'에 'aws-auth' ConfigMap이 없습니다.")
            else:
                print(f"[ERROR] 클러스터 '{cluster_name}'의 'aws-auth' ConfigMap 조회 실패: {e}")
        except Exception as e:
            print(f"[ERROR] 클러스터 '{cluster_name}' 점검 중 예외 발생: {e}")

    if not findings:
        print("[✓ COMPLIANT] 1.11 'system:masters' 그룹에 과도한 권한이 부여된 IAM 주체가 없습니다.")
    else:
        print(f"[⚠ WARNING] 1.11 'system:masters' 그룹에 IAM 주체가 매핑되어 있습니다 ({len(findings)}건).")
        for f in findings:
            print(f"  ├─ 클러스터 '{f['cluster']}'의 {f['type']} '{f['arn']}'이(가) 관리자 그룹에 속해 있습니다.")
    
    return findings

def fix(findings):
    """
    [1.11] EKS 사용자 권한 관리 조치
    - 'aws-auth' ConfigMap에서 'system:masters' 권한을 가진 주체를 제거 (사용자 확인 후)
    """
    if not findings: return

    print("[FIX] 1.11 'aws-auth' ConfigMap에서 'system:masters' 권한 조치를 시작합니다.")
    # 클러스터별로 그룹화
    from collections import defaultdict
    grouped_findings = defaultdict(list)
    for f in findings:
        grouped_findings[f['cluster']].append(f)

    for cluster_name, items in grouped_findings.items():
        if not _update_kubeconfig(cluster_name): continue
        
        if input(f"  -> 클러스터 '{cluster_name}'의 관리자 권한을 수정하시겠습니까? (y/n): ").lower() != 'y':
            continue

        try:
            config.load_kube_config()
            api = client.CoreV1Api()
            cm = api.read_namespaced_config_map(name="aws-auth", namespace="kube-system")
            
            map_roles = yaml.safe_load(cm.data.get("mapRoles", "[]"))
            map_users = yaml.safe_load(cm.data.get("mapUsers", "[]"))
            
            arns_to_remove = {item['arn'] for item in items}
            
            # system:masters 그룹에서 해당 ARN 제거
            new_map_roles = [r for r in map_roles if r['rolearn'] not in arns_to_remove or "system:masters" not in r.get("groups", [])]
            new_map_users = [u for u in map_users if u['userarn'] not in arns_to_remove or "system:masters" not in u.get("groups", [])]

            # ConfigMap 데이터 업데이트
            cm.data['mapRoles'] = yaml.dump(new_map_roles)
            cm.data['mapUsers'] = yaml.dump(new_map_users)

            api.replace_namespaced_config_map(name="aws-auth", namespace="kube-system", body=cm)
            print(f"     [SUCCESS] 클러스터 '{cluster_name}'의 'aws-auth' ConfigMap에서 {len(arns_to_remove)}개의 관리자 주체를 제거했습니다.")

        except Exception as e:
            print(f"     [ERROR] 클러스터 '{cluster_name}' 조치 실패: {e}")

if __name__ == "__main__":
    findings_list = check()
    fix(findings_list)
    