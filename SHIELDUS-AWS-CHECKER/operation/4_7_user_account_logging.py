import boto3
from botocore.exceptions import ClientError

def check():
    """
    [4.7] AWS 사용자 계정 로깅 설정
    - 계정의 모든 활동을 기록하는 Multi-region CloudTrail이 활성화되어 있는지 점검
    """
    print("[INFO] 4.7 AWS 사용자 계정 로깅 설정 체크 중...")
    cloudtrail = boto3.client('cloudtrail')
    
    try:
        is_compliant = any(
            trail.get('IsMultiRegionTrail') and trail.get('IsLogging')
            for trail in cloudtrail.describe_trails().get('trailList', [])
        )
        
        if is_compliant:
            print("[✓ COMPLIANT] 4.7 모든 리전을 기록하는 활성 CloudTrail이 존재합니다.")
        else:
            print("[⚠ WARNING] 4.7 계정의 모든 활동을 기록하는 Multi-region CloudTrail이 없습니다.")
        
        return not is_compliant # 취약하면 True 반환

    except ClientError as e:
        print(f"[ERROR] CloudTrail 정보를 가져오는 중 오류 발생: {e}")
        return False

def fix(is_non_compliant):
    """
    [4.7] AWS 사용자 계정 로깅 설정 조치
    - Multi-region Trail 생성을 안내 (자동 생성은 S3 버킷, SNS 등 부가 리소스 설정이 복잡)
    """
    if not is_non_compliant: return

    print("[FIX] 4.7 Multi-region CloudTrail 생성은 S3 버킷 생성 및 정책 설정이 필요하여 자동화되지 않습니다.")
    print("  └─ AWS 콘솔에서 아래 절차에 따라 수동으로 생성하는 것을 강력히 권장합니다.")
    print("  └─ 1. CloudTrail 서비스로 이동하여 [추적(Trail)] > [추적 생성]을 클릭합니다.")
    print("  └─ 2. 추적 이름(예: management-events-trail)을 입력하고, [모든 리전에 적용] 옵션을 **'예'**로 선택합니다.")
    print("  └─ 3. 관리 이벤트는 '모두'로, 데이터 이벤트나 인사이트 이벤트는 필요에 따라 선택합니다.")
    print("  └─ 4. 로그를 저장할 새 S3 버킷을 생성하도록 선택하거나 기존 버킷을 지정합니다.")
    print("  └─ 5. [다음]을 눌러 검토 후 추적을 생성합니다.")

if __name__ == "__main__":
    non_compliant = check()
    fix(non_compliant)