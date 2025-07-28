import boto3
from botocore.exceptions import ClientError

def check():
    """
    [1.7] Admin Console 루트 계정 사용 관리
    - 루트 계정에 Access Key가 생성되어 있는지 점검하고, 존재 여부를 boolean으로 반환.
    - 루트 계정의 서비스 용도 사용 여부는 별도의 수동 확인이 필요함을 안내.
    """
    print("[INFO] 1.7 Admin Console 루트 계정 사용 관리 체크 중...")
    iam = boto3.client('iam')
    root_key_exists = False

    # 이 항목의 점검은 기술적인 확인과 정책적인 확인이 모두 필요함을 먼저 안내합니다.
    print(f"[ⓘ MANUAL] 루트 계정의 콘솔 사용이 서비스/관리 용도인지 수동 확인이 필요합니다.")

    try:
        summary = iam.get_account_summary()
        if summary['SummaryMap'].get('AccountAccessKeysPresent') == 1:
            print("[⚠ WARNING] 1.7 루트 계정에 Access Key가 존재합니다.")
            root_key_exists = True
        else:
            print("[INFO] 1.7 루트 계정에 Access Key가 생성되어 있지 않습니다.")

    except ClientError as e:
        print(f"[ERROR] 계정 요약 정보를 가져오는 중 오류 발생: {e}")
    
    # fix 함수에 전달할 수 있도록 boolean 값을 반환합니다.
    return root_key_exists

def fix(root_key_exists):
    """
    [1.7] Admin Console 루트 계정 사용 관리 조치
    - 루트 Access Key가 존재하는 경우, 자동 조치 대신 상세하고 안전한 수동 조치 가이드를 제공합니다.
    """
    if not root_key_exists:
        return

    print("\n" + "="*70)
    print("[FIX] 1.7 루트 Access Key 조치 가이드")
    print("="*70)
    print("조치 방법:")
    print("  1. 루트 계정으로 AWS Management Console에 로그인합니다.")
    print("  2. 우측 상단 계정명 클릭 > '보안 자격 증명' > 'Access Key'로 이동합니다.")
    print("  3. 사용 중인 Access Key가 있다면 즉시 '비활성화'하거나, 가능하면 완전히 삭제합니다.")
    print("  4. 루트 계정에 MFA가 적용되어 있는지 추가로 확인합니다.")
    print("\n💡 루트 계정은 계정 관리 용도로만 제한적으로 사용하고, 서비스 운영에는 개별 IAM 사용자를 활용하세요.")
    print("="*70)

if __name__ == "__main__":
    key_exists = check()
    fix(key_exists)