"""
[3.10] ELB 제어 정책 체커
원본: SHIELDUS-AWS-CHECKER/virtual_resources/3_10_elb_connection.py
"""

import boto3
from botocore.exceptions import ClientError
from app.checkers.base_checker import BaseChecker


class ElbConnectionChecker(BaseChecker):
    def __init__(self, session=None):
        super().__init__(session)
        
    @property
    def item_code(self):
        return "3.10"
    
    @property 
    def item_name(self):
        return "ELB 제어 정책 관리"
        
    def run_diagnosis(self):
        """
        [3.10] ELB 제어 정책 점검
        - ALB/NLB/CLB의 다양한 보안 정책 준수 여부 점검
        """
        print("[INFO] 3.10 ELB 제어 정책 점검을 시작합니다...")
        findings = []
        elbv2 = self.session.client('elbv2')
        elb = self.session.client('elb')
        wafv2 = self.session.client('wafv2')

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
        except ClientError as e: 
            print(f"[ERROR] elbv2 점검 중 오류: {e}")

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

        except ClientError as e: 
            print(f"[ERROR] elb(Classic) 점검 중 오류: {e}")

        if not findings: 
            print("[✓ COMPLIANT] 모든 ELB 리소스가 점검된 보안 정책을 준수합니다.")
        else:
            print(f"[⚠ WARNING] 보안 정책 미준수 항목 발견됨: {len(findings)}건")
            unique_findings = {f"{f['lb_name']}:{f['check_id']}": f for f in findings}.values()
            for f in unique_findings: 
                print(f"  ├─ LB '{f['lb_name']}': 정책 {f['check_id']} 위반 - {f['issue']}")

        has_issues = len(findings) > 0
        risk_level = self.calculate_risk_level(len(findings))
        
        return {
            'status': 'success',
            'has_issues': has_issues,
            'risk_level': risk_level,
            'message': f"ELB 보안 정책 위반 {len(findings)}건 발견" if has_issues else "모든 ELB 리소스가 보안 정책을 준수합니다",
            'findings': findings,
            'summary': f"총 {len(findings)}개의 ELB 보안 정책 위반이 발견되었습니다." if has_issues else "모든 ELB 리소스가 안전합니다.",
            'details': {
                'total_findings': len(findings),
                'findings_by_check_id': self._group_findings_by_check_id(findings),
                'affected_load_balancers': len(set(f['lb_name'] for f in findings))
            }
        }

    def _group_findings_by_check_id(self, findings):
        """체크 ID별로 발견사항 그룹화"""
        grouped = {}
        for finding in findings:
            check_id = finding['check_id']
            if check_id not in grouped:
                grouped[check_id] = []
            grouped[check_id].append(finding)
        return grouped

    def execute_fix(self, selected_items):
        """
        [3.10] ELB 제어 정책 조치
        - 복잡한 ELB 설정이므로 대부분 수동 조치 가이드 제공
        """
        if not selected_items:
            return {'status': 'no_action', 'message': '선택된 항목이 없습니다.'}

        # 진단 재실행으로 최신 데이터 확보
        diagnosis_result = self.run_diagnosis()
        if diagnosis_result['status'] != 'success' or not diagnosis_result.get('findings'):
            return {'status': 'no_action', 'message': '조치할 ELB 보안 정책 위반이 없습니다.'}

        print("[FIX] 3.10 로드 밸런서 보안 설정 조치를 시작합니다.")
        print("[ⓘ MANUAL] ELB 보안 설정은 복잡하고 서비스에 영향을 미칠 수 있어 대부분 수동 조치가 필요합니다.")

        return {
            'status': 'manual_required',
            'message': 'ELB 보안 정책 설정은 복잡한 수동 조치가 필요합니다.',
            'manual_guide': self._get_manual_guide()
        }

    def _get_manual_guide(self):
        """수동 조치 가이드 반환"""
        return {
            'title': 'ELB 보안 정책 수동 조치 가이드',
            'description': 'ELB 보안 설정은 서비스 중단을 방지하기 위해 신중한 수동 조치가 필요합니다.',
            'steps': [
                {
                    'type': 'warning',
                    'title': '[주의] 수동 조치 필요',
                    'content': 'ELB 설정 변경은 트래픽에 영향을 미칠 수 있으므로 자동 조치를 지원하지 않습니다.'
                },
                {
                    'type': 'step',
                    'title': '1. HTTP → HTTPS 리디렉션 설정 (ELB.1)',
                    'content': 'ALB 콘솔에서 HTTP 리스너의 기본 작업을 HTTPS로 리디렉션하도록 설정하세요.'
                },
                {
                    'type': 'step',
                    'title': '2. ACM 인증서 적용 (ELB.2)',
                    'content': 'ACM에서 인증서를 발급받고 Classic ELB의 HTTPS 리스너에 적용하세요.'
                },
                {
                    'type': 'step',
                    'title': '3. HTTPS/SSL 리스너 추가 (ELB.3)',
                    'content': 'Classic ELB에 ACM 인증서를 사용하는 HTTPS/SSL 리스너를 추가하세요.'
                },
                {
                    'type': 'step',
                    'title': '4. 잘못된 HTTP 헤더 제거 활성화 (ELB.4)',
                    'content': 'ALB 속성에서 "Drop Invalid Headers"를 활성화하세요.'
                },
                {
                    'type': 'step',
                    'title': '5. 액세스 로깅 활성화 (ELB.5)',
                    'content': 'S3 버킷을 생성하고 ELB 액세스 로깅을 활성화하세요.'
                },
                {
                    'type': 'step',
                    'title': '6. 삭제 방지 활성화 (ELB.6)',
                    'content': 'ALB/NLB 속성에서 삭제 방지를 활성화하세요.'
                },
                {
                    'type': 'step',
                    'title': '7. Connection Draining 활성화 (ELB.7)',
                    'content': 'Classic ELB에서 Connection Draining을 활성화하세요.'
                },
                {
                    'type': 'step',
                    'title': '8. Cross-Zone Load Balancing 활성화 (ELB.9)',
                    'content': 'Classic ELB에서 Cross-Zone Load Balancing을 활성화하세요.'
                },
                {
                    'type': 'step',
                    'title': '9. Multi-AZ 구성 (ELB.10/13)',
                    'content': 'ELB가 최소 2개 이상의 가용 영역에 연결되도록 서브넷을 추가하세요.'
                },
                {
                    'type': 'step',
                    'title': '10. WAF 연결 (ELB.16)',
                    'content': 'ALB에 AWS WAF를 생성하고 연결하여 웹 애플리케이션을 보호하세요.'
                },
                {
                    'type': 'info',
                    'title': '[참고] ELB 보안 모범 사례',
                    'content': 'HTTPS 사용, 액세스 로깅, Multi-AZ 구성, WAF 적용이 ELB 보안의 핵심입니다.'
                }
            ]
        }

    def get_fix_options(self, diagnosis_result):
        """수동 조치 옵션 반환"""
        if not diagnosis_result.get('findings'):
            return []
            
        findings = diagnosis_result.get('findings', [])
        findings_by_check = self._group_findings_by_check_id(findings)
        
        return [{
            'id': 'manual_elb_security_fix',
            'title': 'ELB 보안 정책 수동 조치',
            'description': 'ELB 보안 설정을 수동으로 수정합니다. (서비스 영향 방지를 위한 수동 조치)',
            'is_manual': True,
            'items': [
                {
                    'id': f"check_{check_id}",
                    'name': f"정책 {check_id} 위반 ({len(check_findings)}건)",
                    'description': f"영향받는 로드밸런서: {', '.join(set(f['lb_name'] for f in check_findings))}"
                }
                for check_id, check_findings in findings_by_check.items()
            ]
        }]