#  4.operation/4_4_transit_encryption.py
def check():
    """
    [4.4] 통신구간 암호화 설정 (수동 점검 안내)
    """
    print("[INFO] 4.4 통신구간 암호화 설정 체크 중...")
    print("[ⓘ MANUAL] 통신구간 암호화는 서비스 구성에 따라 달라지므로 자동 점검이 제한됩니다.")
    print("  ├─ 점검 1: [3.10 ELB 연결 관리] 항목을 통해 로드 밸런서의 HTTPS/TLS 리스너 및 리디렉션 설정을 확인하세요.")
    print("  ├─ 점검 2: CloudFront 배포가 있다면, Viewer Protocol Policy가 'Redirect HTTP to HTTPS' 또는 'HTTPS Only'인지 확인하세요.")
    print("  └─ 점검 3: 애플리케이션 간 직접 통신 시 TLS가 적용되었는지 코드 및 구성 레벨에서 확인하세요.")
    return True

def fix(manual_check_required):
    """
    [4.4] 통신구간 암호화 설정 조치 (수동 조치 안내)
    """
    if not manual_check_required: return
    
    print("[FIX] 4.4 통신구간 암호화 조치 가이드입니다.")
    print("  └─ [ELB/ALB] 3.10 항목의 fix 가이드를 참고하여 HTTP 리스너를 HTTPS로 리디렉션하도록 수정하세요.")
    print("  └─ [CloudFront] 배포판의 [Behaviors] 탭에서 'Viewer Protocol Policy'를 'Redirect HTTP to HTTPS'로 변경하세요.")
    print("  └─ [애플리케이션] 내부 통신에 mTLS(상호 TLS)를 적용하거나, 서비스 메쉬(예: Istio, App Mesh)를 사용하여 통신 암호화를 강제하는 것을 고려하세요.")

if __name__ == "__main__":
    required = check()
    fix(required)