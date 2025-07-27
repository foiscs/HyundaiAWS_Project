# 4.operation/4_8_instance_logging.py
def check():
    """
    [4.8] 인스턴스 로깅 설정 (수동 점검 안내)
    """
    print("[INFO] 4.8 인스턴스 로깅 설정 체크 중...")
    print("[ⓘ MANUAL] EC2 인스턴스 내부의 로그 설정은 자동 점검이 불가능합니다.")
    print("  └─ CloudWatch 콘솔의 로그 그룹 목록에 EC2 인스턴스 관련 로그(예: /var/log/messages)가 수집되고 있는지 확인하세요.")
    return True

def fix(manual_check_required):
    """
    [4.8] 인스턴스 로깅 설정 조치 (수동 조치 안내)
    """
    if not manual_check_required: return
        
    print("[FIX] 4.8 EC2 인스턴스 로깅 설정 가이드입니다.")
    print("  └─ 1. EC2 인스턴스에 CloudWatch Logs Agent를 전송할 수 있는 IAM 역할(CloudWatchAgentServerPolicy)을 연결합니다.")
    print("  └─ 2. Systems Manager(SSM) Distributor를 사용하거나 직접 접속하여 인스턴스에 CloudWatch Agent를 설치합니다.")
    print("  └─ 3. Agent 구성 파일(/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json)을 생성하여 수집할 로그 파일 경로를 지정합니다.")
    print("  └─ 4. Agent를 시작하여 로그 수집을 개시합니다: sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c file:/path/to/config.json")

if __name__ == "__main__":
    required = check()
    fix(required)