def check():
    """
    [3.9] EKS Pod 보안 정책 관리 (수동 점검 안내)
    """
    print("[INFO] 3.9 EKS Pod 보안 정책 관리 체크 중...")
    print("[ⓘ MANUAL] 이 항목은 Kubernetes 리소스 확인이 필요하여 자동 점검이 제한됩니다.")
    print("  └─ 점검 명령어: kubectl get namespaces --show-labels")
    print("  └─ 점검사항: 'pod-security.kubernetes.io/enforce' 레이블이 'privileged'로 설정되었거나, 레이블 자체가 없는 네임스페이스가 있는지 확인하세요.")
    return True

def fix(manual_check_required):
    """
    [3.9] EKS Pod 보안 정책 관리 조치 (수동 조치 안내)
    """
    if not manual_check_required:
        return
        
    print("[FIX] 3.9 Pod Security Standards(PSS) 적용 가이드입니다.")
    print("  └─ 네임스페이스에 보안 레이블을 적용하여 해당 네임스페이스의 Pod 보안 수준을 강제할 수 있습니다.")
    print("  └─ [권장] 'baseline' 또는 'restricted' 프로필을 사용하세요.")
    print("  └─ 조치 명령어 (예시): kubectl label --overwrite ns <네임스페이스명> pod-security.kubernetes.io/enforce=baseline")
    print("  └─ `enforce` (강제), `audit` (감사), `warn` (경고) 모드를 각각 설정할 수 있습니다.")

if __name__ == "__main__":
    required = check()
    fix(required)