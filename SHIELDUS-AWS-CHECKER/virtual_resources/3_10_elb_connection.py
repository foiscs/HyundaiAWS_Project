import boto3
from botocore.exceptions import ClientError
import json
import time


def _verify_elb_log_permissions(s3_client, bucket_name, region, account_id):
    """S3 버킷에 ELB 로그 권한이 있는지 확인"""
    try:
        policy_str = s3_client.get_bucket_policy(Bucket=bucket_name)['Policy']
        policy = json.loads(policy_str)
        
        elb_accounts = {'ap-northeast-2': '600734575887', 'us-east-1': '127311923021'} # Add more regions if needed
        elb_account_id = elb_accounts.get(region)
        if not elb_account_id: return False

        expected_principal = f"arn:aws:iam::{elb_account_id}:root"
        expected_resource = f"arn:aws:s3:::{bucket_name}/AWSLogs/{account_id}/*"

        for stmt in policy.get("Statement", []):
            if stmt.get("Effect") == "Allow" and \
               stmt.get("Principal", {}).get("AWS") == expected_principal and \
               stmt.get("Action") == "s3:PutObject" and \
               stmt.get("Resource") == expected_resource:
                return True
    except ClientError as e:
        if e.response['Error']['Code'] != 'NoSuchBucketPolicy':
            print(f"     [WARNING] 버킷 정책 확인 중 오류: {e}")
    return False

def _setup_elb_log_permissions(s3_client, bucket_name, region, account_id):
    """S3 버킷에 ELB 로그 권한을 설정"""
    try:
        elb_accounts = {'ap-northeast-2': '600734575887', 'us-east-1': '127311923021'} # Add more regions if needed
        elb_account_id = elb_accounts.get(region)
        if not elb_account_id:
            print(f"     [ERROR] 리전 '{region}'의 ELB 서비스 계정 ID를 알 수 없어 정책을 설정할 수 없습니다.")
            return False

        policy = {
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Principal": {"AWS": f"arn:aws:iam::{elb_account_id}:root"}, "Action": "s3:PutObject", "Resource": f"arn:aws:s3:::{bucket_name}/AWSLogs/{account_id}/*"}]
        }
        s3_client.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(policy))
        print(f"     [SUCCESS] 버킷 '{bucket_name}'에 ELB 로깅 권한 정책을 설정했습니다.")
        return True
    except Exception as e:
        print(f"     [ERROR] 권한 설정 중 오류: {e}")
        return False

def _create_elb_log_bucket(s3_client, region, account_id):
    """ELB 로그용 새 S3 버킷을 생성하는 함수"""
    try:
        bucket_name = f"elb-logs-{account_id}-{region}-{str(int(time.time()))[-6:]}"
        print(f"     버킷 '{bucket_name}' 생성 중...")
        if region == 'us-east-1': s3_client.create_bucket(Bucket=bucket_name)
        else: s3_client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': region})
        
        if _setup_elb_log_permissions(s3_client, bucket_name, region, account_id):
            return bucket_name
        else:
            print(f"     [ERROR] 버킷은 생성되었지만 권한 설정에 실패했습니다.")
            return None # 권한 설정 실패 시 None 반환
    except ClientError as e:
        print(f"     [ERROR] 버킷 생성 중 오류: {e}")
        return None

def _select_s3_bucket_for_logging():
    """ALB 로깅용 S3 버킷을 선택하거나 생성하는 헬퍼 함수"""
    s3, sts, region = boto3.client('s3'), boto3.client('sts'), boto3.Session().region_name
    account_id = sts.get_caller_identity()['Account']
    
    try:
        buckets = s3.list_buckets()['Buckets']
        while True:
            print("\n     사용 가능한 S3 버킷 목록:")
            for i, b in enumerate(buckets, 1): print(f"     {i}. {b['Name']}")
            print(f"     {len(buckets) + 1}. 새 버킷 생성")
            choice_str = input("     로깅을 저장할 버킷을 선택하세요 (번호 입력, 0=취소): ").strip()
            
            if not choice_str.isdigit(): print("     [ERROR] 숫자를 입력하세요."); continue
            choice = int(choice_str)

            if choice == 0: return None
            elif 1 <= choice <= len(buckets):
                selected_bucket = buckets[choice - 1]['Name']
                # <-- 수정된 부분: 기존 버킷 선택 시 권한 확인 및 설정 로직 추가 -->
                if _verify_elb_log_permissions(s3, selected_bucket, region, account_id):
                    return selected_bucket
                else:
                    print(f"     [WARNING] 버킷 '{selected_bucket}'에 ELB 로깅 권한이 없습니다.")
                    if input("     지금 권한을 자동으로 설정하시겠습니까? (y/n): ").lower() == 'y':
                        if _setup_elb_log_permissions(s3, selected_bucket, region, account_id):
                            return selected_bucket
                    print("     [INFO] 권한이 설정되지 않은 버킷은 사용할 수 없습니다. 다른 버킷을 선택하세요.")
                    continue # 권한 설정 안하면 다시 선택
            elif choice == len(buckets) + 1:
                return _create_elb_log_bucket(s3, region, account_id)
            else:
                print("     [ERROR] 올바른 번호를 입력하세요.")
    except ClientError as e:
        print(f"     [ERROR] S3 버킷 목록 조회 중 오류: {e}")
        return None
# (WAF 관련 헬퍼 함수는 이전과 동일)
def _select_waf_for_alb():
    wafv2 = boto3.client('wafv2')
    try:
        regional_wafs = wafv2.list_web_acls(Scope='REGIONAL')['WebACLs']
        if not regional_wafs:
            if input("     [INFO] 계정에 리전용 WAF가 없습니다. 기본 WAF를 생성하시겠습니까? (y/n): ").lower() == 'y': return _create_basic_waf()
            else: return None
        
        print("     사용 가능한 WAF 목록:")
        for i, waf in enumerate(regional_wafs, 1): print(f"     {i}. {waf['Name']}")
        print(f"     {len(regional_wafs) + 1}. 새 WAF 생성")
        choice = input("     선택하세요 (번호 입력, 0=취소): ").strip()
        if choice == '0' or not choice.isdigit(): return None
        
        choice_num = int(choice)
        if 1 <= choice_num <= len(regional_wafs): return regional_wafs[choice_num - 1]['ARN']
        elif choice_num == len(regional_wafs) + 1: return _create_basic_waf()
        else: print("     [ERROR] 올바른 번호를 입력하세요."); return None
    except ClientError as e: print(f"     [ERROR] WAF 목록 조회 중 오류: {e}"); return None

def _create_basic_waf():
    wafv2 = boto3.client('wafv2')
    try:
        waf_name = f"Shieldus-BasicWAF-{str(int(time.time()))[-6:]}"
        print(f"     WAF '{waf_name}' 생성 중...")
        response = wafv2.create_web_acl(
            Name=waf_name, Scope='REGIONAL', DefaultAction={'Allow': {}},
            Rules=[{
                'Name': 'AWSManagedRulesCommonRuleSet', 'Priority': 1, 'OverrideAction': {'None': {}},
                'VisibilityConfig': {'SampledRequestsEnabled': True, 'CloudWatchMetricsEnabled': True, 'MetricName': 'CommonRuleSet'},
                'Statement': {'ManagedRuleGroupStatement': {'VendorName': 'AWS', 'Name': 'AWSManagedRulesCommonRuleSet'}}
            }],
            VisibilityConfig={'SampledRequestsEnabled': True, 'CloudWatchMetricsEnabled': True, 'MetricName': waf_name}
        )
        waf_arn = response['Summary']['ARN']
        print(f"     [SUCCESS] WAF '{waf_arn}' 생성 완료. (적용까지 시간이 걸릴 수 있음)")
        return waf_arn
    except ClientError as e: print(f"     [ERROR] WAF 생성 중 오류: {e}"); return None

# --- Main Check & Fix Functions (이전과 동일) ---
def check():
    print("[INFO] 3.10 ELB 제어 정책 점검을 시작합니다...")
    findings = []
    elbv2 = boto3.client('elbv2')
    elb = boto3.client('elb')
    wafv2 = boto3.client('wafv2')

    # ----------- ELBv2 (ALB, NLB) 점검 -----------
    try:
        for lb in elbv2.describe_load_balancers()['LoadBalancers']:
            lb_arn, lb_name = lb['LoadBalancerArn'], lb['LoadBalancerName']
            attrs = {a['Key']: a['Value'] for a in elbv2.describe_load_balancer_attributes(LoadBalancerArn=lb_arn)['Attributes']}

            # ELB.1: HTTP 리스너 -> HTTPS 리디렉션
            for l in elbv2.describe_listeners(LoadBalancerArn=lb_arn)['Listeners']:
                if l['Protocol'] == 'HTTP' and not any(a.get('Type') == 'redirect' and a.get('RedirectConfig', {}).get('Protocol') == 'HTTPS' for a in l.get('DefaultActions', [])):
                    findings.append({'lb_name': lb_name, 'check_id': 'ELB.1', 'issue': 'HTTP 리스너가 HTTPS로 리디렉션되지 않음', 'lb_arn': lb_arn, 'listener_arn': l['ListenerArn']})

            # ELB.4: 잘못된 HTTP 헤더 제거 설정
            if lb['Type'] == 'application' and attrs.get('routing.http.drop_invalid_header_fields.enabled') != 'true':
                findings.append({'lb_name': lb_name, 'check_id': 'ELB.4', 'issue': '잘못된 HTTP 헤더 제거 비활성', 'lb_arn': lb_arn})

            # ELB.5: 로깅 활성화
            if attrs.get('access_logs.s3.enabled') != 'true':
                findings.append({'lb_name': lb_name, 'check_id': 'ELB.5', 'issue': 'ALB/NLB 로깅 비활성', 'lb_arn': lb_arn})
            
            # ELB.6: 삭제 방지
            if attrs.get('deletion_protection.enabled') != 'true':
                findings.append({'lb_name': lb_name, 'check_id': 'ELB.6', 'issue': '삭제 방지 비활성', 'lb_arn': lb_arn})

            # ELB.10/13: 최소 2개 AZ
            if len(lb.get('AvailabilityZones', [])) < 2:
                findings.append({'lb_name': lb_name, 'check_id': 'ELB.10/13', 'issue': '2개 미만 가용영역에 연결됨', 'lb_arn': lb_arn})

            # ELB.16: WAF 연결
            if lb['Type'] == 'application':
                try:
                    wafv2.get_web_acl_for_resource(ResourceArn=lb_arn)
                except wafv2.exceptions.WAFNonexistentItemException:
                    findings.append({'lb_name': lb_name, 'check_id': 'ELB.16', 'issue': 'WAF 연결 안됨', 'lb_arn': lb_arn})
    except ClientError as e: print(f"[ERROR] elbv2 점검 중 오류: {e}")

    # ----------- Classic ELB 점검 -----------
    try:
        for clb in elb.describe_load_balancers()['LoadBalancerDescriptions']:
            lb_name = clb['LoadBalancerName']
            attrs = elb.describe_load_balancer_attributes(LoadBalancerName=lb_name)['LoadBalancerAttributes']
            listeners = clb.get('ListenerDescriptions', [])

            # ELB.2 & ELB.8: ACM 인증서 및 최신 보안 정책 사용
            for l_desc in listeners:
                l = l_desc['Listener']
                if l['Protocol'] in ['HTTPS', 'SSL']:
                    if 'arn:aws:acm' not in l.get('SSLCertificateId', ''):
                        findings.append({'lb_name': lb_name, 'check_id': 'ELB.2', 'issue': 'ACM 인증서 미사용'})
                    if not l_desc.get('PolicyNames'):
                        findings.append({'lb_name': lb_name, 'check_id': 'ELB.8', 'issue': f"HTTPS 리스너(포트:{l['LoadBalancerPort']})에 보안 정책 없음"})

            # ELB.3: HTTPS/SSL 리스너 존재
            if not any(l['Listener']['Protocol'] in ['HTTPS', 'SSL'] for l in listeners):
                findings.append({'lb_name': lb_name, 'check_id': 'ELB.3', 'issue': 'HTTPS/SSL 리스너 없음'})

            # ELB.5: 로깅 활성화
            if not attrs.get('AccessLog', {}).get('Enabled', False):
                findings.append({'lb_name': lb_name, 'check_id': 'ELB.5', 'issue': 'CLB 로깅 비활성'})

            # ELB.7: Connection Draining
            if not attrs.get('ConnectionDraining', {}).get('Enabled', False):
                findings.append({'lb_name': lb_name, 'check_id': 'ELB.7', 'issue': 'Connection Draining 비활성'})

            # ELB.9: Cross-Zone Load Balancing
            if not attrs.get('CrossZoneLoadBalancing', {}).get('Enabled', False):
                findings.append({'lb_name': lb_name, 'check_id': 'ELB.9', 'issue': 'Cross-Zone LB 비활성'})

            # ELB.10: 최소 2개 AZ
            if len(clb['AvailabilityZones']) < 2:
                findings.append({'lb_name': lb_name, 'check_id': 'ELB.10', 'issue': '2개 미만 가용영역 연결'})

    except ClientError as e: print(f"[ERROR] elb(Classic) 점검 중 오류: {e}")

    if not findings: print("[✓ COMPLIANT] 모든 ELB 리소스가 점검된 보안 정책을 준수합니다.")
    else:
        print(f"[⚠ WARNING] 보안 정책 미준수 항목 발견됨: {len(findings)}건")
        unique_findings = {f"{f['lb_name']}:{f['check_id']}": f for f in findings}.values()
        for f in unique_findings: print(f"  ├─ LB '{f['lb_name']}': 정책 {f['check_id']} 위반 - {f['issue']}")
    return findings

def fix(findings):
    if not findings: return
    elbv2, elb = boto3.client('elbv2'), boto3.client('elb')
    print("[FIX] 3.10 로드 밸런서 보안 설정 조치를 시작합니다.")
    processed = set()

    for f in findings:
        key = f"{f['lb_name']}:{f['check_id']}"
        if key in processed: continue
        
        lb_name, check_id, lb_arn = f['lb_name'], f['check_id'], f.get('lb_arn')
        
        if check_id == 'ELB.1':
            if input(f"  -> ALB '{lb_name}'의 HTTP 리스너를 HTTPS로 리디렉션하시겠습니까? (y/n): ").lower() == 'y':
                try:
                    elbv2.modify_listener(ListenerArn=f['listener_arn'], DefaultActions=[{'Type': 'redirect', 'RedirectConfig': {'Protocol': 'HTTPS', 'Port': '443', 'StatusCode': 'HTTP_301'}}])
                    print(f"     [SUCCESS] 리디렉션을 설정했습니다.")
                except ClientError as e: print(f"     [ERROR] 실패: {e}")
        
        elif check_id in ['ELB.2', 'ELB.3', 'ELB.8', 'ELB.10', 'ELB.10/13']:
            print(f"  -> LB '{lb_name}'의 정책 '{check_id}' 위반은 자동 조치가 복잡하거나 위험합니다. 수동 조치를 권장합니다.")
            if check_id == 'ELB.2': print("     └─ [가이드] ACM에서 새 인증서를 발급받고 CLB 리스너에서 교체하세요.")
            if check_id == 'ELB.3': print("     └─ [가이드] CLB에 ACM 인증서를 사용하여 HTTPS/SSL 리스너를 추가하세요.")
            if check_id == 'ELB.8': print(f"     └─ [가이드] CLB 리스너의 보안 정책을 최신 권장 정책(예: ELBSecurityPolicy-TLS-1-2-2017-01)으로 변경하세요.")
            if 'ELB.10' in check_id: print("     └─ [가이드] ELB 설정에서 다른 가용 영역의 서브넷을 추가하여 Multi-AZ를 구성하세요.")

        elif check_id == 'ELB.4':
            if input(f"  -> ALB '{lb_name}'에 '잘못된 헤더 필드 삭제'를 활성화하시겠습니까? (y/n): ").lower() == 'y':
                try:
                    elbv2.modify_load_balancer_attributes(LoadBalancerArn=lb_arn, Attributes=[{'Key': 'routing.http.drop_invalid_header_fields.enabled', 'Value': 'true'}])
                    print(f"     [SUCCESS] 설정을 활성화했습니다.")
                except ClientError as e: print(f"     [ERROR] 실패: {e}")

        elif check_id == 'ELB.5':
            if input(f"  -> LB '{lb_name}'에 액세스 로깅을 활성화하시겠습니까? (y/n): ").lower() == 'y':
                bucket = _select_s3_bucket_for_logging()
                if bucket:
                    try:
                        if lb_arn: # ALB/NLB
                            elbv2.modify_load_balancer_attributes(LoadBalancerArn=lb_arn, Attributes=[{'Key': 'access_logs.s3.enabled', 'Value': 'true'}, {'Key': 'access_logs.s3.bucket', 'Value': bucket}])
                        else: # CLB
                            elb.modify_load_balancer_attributes(LoadBalancerName=lb_name, LoadBalancerAttributes={'AccessLog': {'Enabled': True, 'S3BucketName': bucket}})
                        print(f"     [SUCCESS] 로깅을 활성화했습니다.")
                    except ClientError as e: print(f"     [ERROR] 실패: {e}")
        
        elif check_id == 'ELB.6':
            if input(f"  -> ALB '{lb_name}'에 삭제 방지를 활성화하시겠습니까? (y/n): ").lower() == 'y':
                try:
                    elbv2.modify_load_balancer_attributes(LoadBalancerArn=lb_arn, Attributes=[{'Key': 'deletion_protection.enabled', 'Value': 'true'}])
                    print(f"     [SUCCESS] 삭제 방지를 활성화했습니다.")
                except ClientError as e: print(f"     [ERROR] 실패: {e}")

        elif check_id == 'ELB.7':
            if input(f"  -> CLB '{lb_name}'에 Connection Draining을 활성화하시겠습니까? (y/n): ").lower() == 'y':
                try:
                    elb.modify_load_balancer_attributes(LoadBalancerName=lb_name, LoadBalancerAttributes={'ConnectionDraining': {'Enabled': True, 'Timeout': 300}})
                    print(f"     [SUCCESS] Connection Draining을 활성화했습니다.")
                except ClientError as e: print(f"     [ERROR] 실패: {e}")
                
        elif check_id == 'ELB.9':
            if input(f"  -> CLB '{lb_name}'에 Cross-Zone Load Balancing을 활성화하시겠습니까? (y/n): ").lower() == 'y':
                try:
                    elb.modify_load_balancer_attributes(LoadBalancerName=lb_name, LoadBalancerAttributes={'CrossZoneLoadBalancing': {'Enabled': True}})
                    print(f"     [SUCCESS] Cross-Zone Load Balancing을 활성화했습니다.")
                except ClientError as e: print(f"     [ERROR] 실패: {e}")

        elif check_id == 'ELB.16':
            if input(f"  -> ALB '{lb_name}'에 WAF를 연결하시겠습니까? (y/n): ").lower() == 'y':
                waf_arn = _select_waf_for_alb()
                if waf_arn:
                    try:
                        wafv2 = boto3.client('wafv2')
                        wafv2.associate_web_acl(WebACLArn=waf_arn, ResourceArn=lb_arn)
                        print(f"     [SUCCESS] WAF를 연결했습니다.")
                    except ClientError as e: print(f"     [ERROR] 실패: {e}")
        
        processed.add(key)

if __name__ == "__main__":
    findings = check()
    fix(findings)