import boto3
from botocore.exceptions import ClientError
import os, sys

# 상위 디렉토리 경로 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from aws_client import AWSClientManager

def check():
    """
    [4.4] 통신구간 암호화 설정
    - 전송 중 데이터 암호화는 서비스 구성에 따라 달라지므로 수동 점검을 안내
    """
    print("[INFO] 4.4 통신구간 암호화 설정 체크 중...")
    print("[ⓘ MANUAL] 통신구간 암호화는 서비스 구성에 따라 달라지므로 자동 점검이 제한됩니다.")
    print("  ├─ 점검 1: ELB/ALB/NLB 리스너가 HTTPS/TLS를 사용하는지 확인하세요.")
    print("  │ └─ [3.10 ELB 연결 관리] 항목에서 관련 내용을 점검합니다.")
    print("  ├─ 점검 2: CloudFront 배포가 'Redirect HTTP to HTTPS' 또는 'HTTPS Only'로 설정되었는지 확인하세요.")
    print("  ├─ 점검 3: EC2 인스턴스에 직접 접근 시 SSH/RDP 등 암호화된 프로토콜을 사용하는지 확인하세요.")
    print("  └─ 🔧 애플리케이션과 클라이언트 간, 서비스 간 통신에 TLS/SSL을 적용하여 데이터 유출을 방지하세요.")