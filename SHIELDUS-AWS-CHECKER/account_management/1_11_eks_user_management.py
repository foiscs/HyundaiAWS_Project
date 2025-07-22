# 1.account_management/1_11_eks_user_management.py
def check():
    """
    [1.11] EKS 사용자 관리 (수동 점검 안내)
    """
    print("[INFO] 1.11 EKS 사용자 관리 체크 중...")
    print("[ⓘ MANUAL] 이 항목은 Kubernetes API 접근이 필요하여 자동 점검이 제한됩니다.")
    print("  └─ 점검 명령어: kubectl describe configmap aws-auth -n kube-system")
    return True # 항상 수동 조치를 안내하도록 True 반환

def fix(manual_check_required):
    """
    [1.11] EKS 사용자 관리 조치 (수동 조치 안내)
    """
    if not manual_check_required:
        return
    print("[FIX] 1.11 'aws-auth' ConfigMap 조치 가이드입니다.")
    print("  └─ 1. 위 'check' 명령어로 ConfigMap 내용을 확인합니다.")
    print("  └─ 2. 'mapUsers' 및 'mapRoles' 목록에서 불필요한 사용자나 역할을 제거합니다.")
    print("  └─ 3. 특히 'system:masters' 그룹에 매핑된 주체는 최소한으로 유지해야 합니다.")
    print("  └─ 4. 'kubectl edit configmap aws-auth -n kube-system' 명령어로 수정할 수 있습니다.")

if __name__ == "__main__":
    required = check()
    fix(required)