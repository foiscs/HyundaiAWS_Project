# 4.operation/4_8_instance_logging.py
def check():
    """
    [4.8] 인스턴스 로깅 설정 (수동 점검 안내)
    """
    print("[INFO] 4.8 인스턴스 로깅 설정 체크 중...")
    print("[ⓘ MANUAL] EC2 인스턴스 내부의 로그 설정은 자동 점검이 불가능합니다.")
    print("  └─ CloudWatch 콘솔의 로그 그룹 목록에 EC2 인스턴스 관련 로그(예: /var/log/messages)가 수집되고 있는지 확인하세요.")
    return True


# def fix(manual_check_required):
#     """
#     [4.8] 인스턴스 로깅 설정 조치 (수동 조치 안내)
#     """
#     if not manual_check_required: return
        
#     print("[FIX] 4.8 EC2 인스턴스 로깅 설정 가이드입니다.")
#     print("  └─ 1. EC2 인스턴스에 CloudWatch Logs Agent를 전송할 수 있는 IAM 역할(CloudWatchAgentServerPolicy)을 연결합니다.")
#     print("  └─ 2. Systems Manager(SSM) Distributor를 사용하거나 직접 접속하여 인스턴스에 CloudWatch Agent를 설치합니다.")
#     print("  └─ 3. Agent 구성 파일(/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json)을 생성하여 수집할 로그 파일 경로를 지정합니다.")
#     print("  └─ 4. Agent를 시작하여 로그 수집을 개시합니다: sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c file:/path/to/config.json")

# if __name__ == "__main__":
#     required = check()
#     fix(required)

# 4.operation/4_8_instance_logging.py

import boto3

def check():
    logs_client = boto3.client('logs')
    ec2_client = boto3.client('ec2')

    # 1. 모든 CloudWatch 로그 그룹 이름 수집
    log_groups = []
    next_token = None
    while True:
        if next_token:
            response = logs_client.describe_log_groups(nextToken=next_token)
        else:
            response = logs_client.describe_log_groups()
        log_groups.extend(response.get('logGroups', []))
        next_token = response.get('nextToken')
        if not next_token:
            break
    log_group_names = [lg['logGroupName'] for lg in log_groups]

    # 2. EC2 인스턴스 ID 수집
    instances = ec2_client.describe_instances()
    instance_ids = [
        inst['InstanceId']
        for reservation in instances['Reservations']
        for inst in reservation['Instances']
    ]

    # 3. 로그 그룹 이름에 인스턴스 ID 포함 여부로 로깅 여부 확인
    good = [iid for iid in instance_ids if any(iid in lg for lg in log_group_names)]
    bad = list(set(instance_ids) - set(good))

    # 결과 출력
    print("✅ 양호 (CloudWatch 로그 등록됨):", good)
    print("❌ 취약 (로그 등록 안 됨):", bad)

    return {"양호": good, "취약": bad}

# 실행 entry point
if __name__ == "__main__":
    required = check()
    fix(required)