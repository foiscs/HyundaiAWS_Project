def check():
    """
    [1.13] EKS 불필요한 익명 접근 관리 (수동 점검 안내)
    """
    print("[INFO] 1.13 EKS 불필요한 익명 접근 관리 체크 중...")
    print("[ⓘ MANUAL] 이 항목은 Kubernetes 리소스 확인이 필요하여 자동 점검이 제한됩니다.")
    print("  └─ 점검 명령어: kubectl get clusterrolebindings,rolebindings --all-namespaces -o jsonpath='{.items[?(@.subjects[?(@.name==\"system:anonymous\")])]}'")
    return True

def fix(manual_check_required):
    """
    [1.13] EKS 불필요한 익명 접근 관리 조치 (수동 조치 안내)
    """
    if not manual_check_required:
        return
    print("[FIX] 1.13 EKS 익명 접근 권한 조치 가이드입니다.")
    print("  └─ 1. 위 'check' 명령어로 'system:anonymous' 또는 'system:unauthenticated'에 부여된 권한을 확인합니다.")
    print("  └─ 2. 'system:public-info-viewer'와 같이 의도된 바인딩 외에 불필요한 ClusterRoleBinding이나 RoleBinding이 있다면 삭제합니다.")
    print("  └─ 3. 조치 명령어: kubectl delete clusterrolebinding <바인딩_이름>")

if __name__ == "__main__":
    required = check()
    fix(required)