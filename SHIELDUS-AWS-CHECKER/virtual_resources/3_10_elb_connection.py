import boto3
from botocore.exceptions import ClientError

def check():
    """
    [3.10] ELB 연결 관리
    - ALB/NLB/GLB에 대해 주요 보안 설정을 점검 (HTTP 리스너, 로깅, 삭제 방지)
    """
    print("[INFO] 3.10 ELB 연결 관리 체크 중...")
    elbv2 = boto3.client('elbv2')
    findings = []
    
    try:
        for lb in elbv2.describe_load_balancers()['LoadBalancers']:
            lb_arn, lb_name = lb['LoadBalancerArn'], lb['LoadBalancerName']
            attrs = {a['Key']: a['Value'] for a in elbv2.describe_load_balancer_attributes(LoadBalancerArn=lb_arn)['Attributes']}
            
            if attrs.get('access_logs.s3.enabled') != 'true':
                findings.append({'lb_arn': lb_arn, 'lb_name': lb_name, 'issue': '액세스 로깅 비활성'})
            if attrs.get('deletion_protection.enabled') != 'true':
                findings.append({'lb_arn': lb_arn, 'lb_name': lb_name, 'issue': '삭제 방지 비활성'})

            listeners = elbv2.describe_listeners(LoadBalancerArn=lb_arn)['Listeners']
            has_https = any(l['Protocol'] == 'HTTPS' for l in listeners)
            for l in listeners:
                if l['Protocol'] == 'HTTP':
                    is_redirect = any(a.get('Type') == 'redirect' for a in l.get('DefaultActions', []))
                    if not has_https or not is_redirect:
                        findings.append({'lb_arn': lb_arn, 'lb_name': lb_name, 'issue': 'HTTP 리스너 암호화/리디렉션 미흡', 'listener_arn': l['ListenerArn']})

        if not findings:
            print("[✓ COMPLIANT] 3.10 모든 로드 밸런서가 주요 보안 설정을 충족합니다.")
        else:
            # 중복 제거
            unique_findings_display = {f"{f['lb_name']}:{f['issue'].split(' ')[0]}": f for f in findings}
            print(f"[⚠ WARNING] 3.10 로드 밸런서에 보안 설정이 미흡한 항목이 있습니다 ({len(unique_findings_display)}건).")
            for f in unique_findings_display.values(): print(f"  ├─ LB '{f['lb_name']}': {f['issue']}")
        return findings

    except ClientError as e:
        print(f"[ERROR] 로드 밸런서 정보를 가져오는 중 오류 발생: {e}")
        return []

def fix(findings):
    """
    [3.10] ELB 연결 관리 조치
    - 로깅, 삭제 방지, HTTP 리다이렉션 설정
    """
    if not findings:
        return
        
    elbv2 = boto3.client('elbv2')
    print("[FIX] 3.10 로드 밸런서 보안 설정 조치를 시작합니다.")
    
    processed_actions = set()
    for f in findings:
        lb_arn, lb_name, issue = f['lb_arn'], f['lb_name'], f['issue']
        action_key = f"{lb_arn}:{issue.split(' ')[0]}" # LB단위 액션 중복 방지

        if action_key in processed_actions: continue
        
        if '액세스 로깅' in issue:
            if input(f"  -> LB '{lb_name}'에 액세스 로깅을 활성화하시겠습니까? (y/n): ").lower() == 'y':
                bucket = input("     로그 저장용 S3 버킷 이름을 입력하세요: ")
                try:
                    elbv2.modify_load_balancer_attributes(LoadBalancerArn=lb_arn, Attributes=[{'Key': 'access_logs.s3.enabled', 'Value': 'true'}, {'Key': 'access_logs.s3.bucket', 'Value': bucket}])
                    print(f"     [SUCCESS] LB '{lb_name}'의 액세스 로깅을 활성화했습니다.")
                except ClientError as e: print(f"     [ERROR] 실패: {e}")
            processed_actions.add(action_key)
        
        elif '삭제 방지' in issue:
            if input(f"  -> LB '{lb_name}'에 삭제 방지를 활성화하시겠습니까? (y/n): ").lower() == 'y':
                try:
                    elbv2.modify_load_balancer_attributes(LoadBalancerArn=lb_arn, Attributes=[{'Key': 'deletion_protection.enabled', 'Value': 'true'}])
                    print(f"     [SUCCESS] LB '{lb_name}'의 삭제 방지를 활성화했습니다.")
                except ClientError as e: print(f"     [ERROR] 실패: {e}")
            processed_actions.add(action_key)
                
        elif 'HTTP 리스너' in issue:
            if input(f"  -> LB '{lb_name}'의 HTTP 리스너({f['listener_arn'].split('/')[-1]})를 HTTPS로 리디렉션하도록 수정하시겠습니까? (y/n): ").lower() == 'y':
                try:
                    elbv2.modify_listener(ListenerArn=f['listener_arn'], DefaultActions=[{'Type': 'redirect', 'RedirectConfig': {'Protocol': 'HTTPS', 'Port': '443', 'StatusCode': 'HTTP_301'}}])
                    print(f"     [SUCCESS] HTTP 리스너에 리디렉션을 설정했습니다.")
                except ClientError as e: print(f"     [ERROR] 실패: {e}")
            processed_actions.add(action_key)

if __name__ == "__main__":
    findings_list = check()
    fix(findings_list)