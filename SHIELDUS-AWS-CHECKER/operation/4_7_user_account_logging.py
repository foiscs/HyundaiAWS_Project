import boto3
from botocore.exceptions import ClientError
import os, sys

# 상위 디렉토리 경로 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from aws_client import AWSClientManager


# 4.operation/4_7_user_account_logging.py
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
        response = cloudtrail.describe_trails()
        is_multi_region_trail_active = False
        for trail in response.get('trailList', []):
            if trail.get('IsMultiRegionTrail') and trail.get('IsLogging'):
                is_multi_region_trail_active = True
                print(f"[✓ COMPLIANT] 4.7 모든 리전을 기록하는 활성 CloudTrail이 존재합니다 (Trail: {trail['Name']}).")
                break
        
        if not is_multi_region_trail_active:
            print("[⚠ WARNING] 4.7 계정의 모든 활동을 기록하는 Multi-region CloudTrail이 없습니다.")
            print("  └─ 🔧 CloudTrail 서비스에서 [모든 리전에 적용] 옵션을 활성화한 새 추적을 생성하여 계정 전체의 API 활동을 기록하세요.")

    except ClientError as e:
        print(f"[ERROR] CloudTrail 정보를 가져오는 중 오류 발생: {e}")