def check():
    """
    [1.12] EKS 서비스 어카운트 관리 (수동 점검 안내)
    """
    print("[INFO] 1.12 EKS 서비스 어카운트 관리 체크 중...")
    print("[ⓘ MANUAL] 이 항목은 Kubernetes 리소스 확인이 필요하여 자동 점검이 제한됩니다.")
    print("  └─ 점검 명령어 (기본 SA 확인): kubectl get serviceaccount default -n <네임스페이스> -o yaml")
    return True

def fix(manual_check_required):
    """
    [1.12] EKS 서비스 어카운트 관리 조치 (수동 조치 안내)
    """
    if not manual_check_required:
        return
    print("[FIX] 1.12 Service Account 토큰 자동 마운트 비활성화 조치 가이드입니다.")
    print("  └─ Kubernetes API 접근이 필요 없는 애플리케이션의 보안을 강화하기 위해 토큰 마운트를 비활성화하세요.")
    print("  └─ 방법 1 (Pod 단위): Pod spec에 `automountServiceAccountToken: false` 추가")
    print("  └─ 방법 2 (ServiceAccount 단위): ServiceAccount manifest에 `automountServiceAccountToken: false` 추가")
    print("  └─ 조치 명령어 예시: kubectl patch serviceaccount default -n <네임스페이스> -p '{\"automountServiceAccountToken\": false}'")

if __name__ == "__main__":
    required = check()
    fix(required)