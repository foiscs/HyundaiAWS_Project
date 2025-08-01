"""
[3.3] 네트워크 ACL 인/아웃바운드 트래픽 정책 관리 체커
원본: SHIELDUS-AWS-CHECKER/virtual_resources/3_3_nacl_traffic_policy.py
"""

import boto3
from botocore.exceptions import ClientError
from app.checkers.base_checker import BaseChecker


class NaclTrafficPolicyChecker(BaseChecker):
    def __init__(self, session=None):
        super().__init__(session)
        
    @property
    def item_code(self):
        return "3.3"
    
    @property 
    def item_name(self):
        return "네트워크 ACL 인/아웃바운드 트래픽 정책 관리"
        
    def run_diagnosis(self):
        """
        [3.3] 네트워크 ACL 인/아웃바운드 트래픽 정책 관리
        - 모든 트래픽을 허용하는 광범위 규칙이 있는지 점검 (프로토콜 -1, 포트 전체, CIDR 0.0.0.0/0, Allow)
        """
        print("[INFO] 3.3 네트워크 ACL 트래픽 정책 관리 체크 중...")
        ec2 = self.session.client('ec2')
        vulnerable_nacls = []

        try:
            # 1. 모든 네트워크 ACL 조회
            nacls = ec2.describe_network_acls()['NetworkAcls']
            for nacl in nacls:
                for entry in nacl['Entries']:
                    # 2. 규칙 필드 수집
                    rule_num = entry.get('RuleNumber')
                    protocol = entry.get('Protocol')
                    rule_action = entry.get('RuleAction')
                    cidr = entry.get('CidrBlock', '')
                    egress = entry.get('Egress', False)
                    port_range = entry.get('PortRange', {})

                    # 3. 점검 조건
                    is_all_protocol = protocol == '-1'
                    is_all_port = port_range == {}  # 포트 범위 전체 허용 (없으면 전체 허용)
                    is_all_cidr = cidr == '0.0.0.0/0'
                    is_allow = rule_action == 'allow'

                    if is_all_protocol and is_all_port and is_all_cidr and is_allow:
                        direction = "아웃바운드" if egress else "인바운드"
                        vulnerable_nacls.append({
                            "NaclId": nacl['NetworkAclId'],
                            "RuleNumber": rule_num,
                            "Direction": direction,
                            "Egress": egress
                        })

            # 4. 결과 출력
            if not vulnerable_nacls:
                print("[✓ COMPLIANT] 3.3 모든 트래픽을 허용하는 광범위한 NACL 규칙이 없습니다.")
            else:
                print(f"[⚠ WARNING] 3.3 모든 트래픽을 허용하는 광범위한 NACL 규칙이 존재합니다 ({len(vulnerable_nacls)}건).")
                for f in vulnerable_nacls:
                    print(f"  ├─ NACL '{f['NaclId']}'에 모든 {f['Direction']} 트래픽 허용 규칙(#{f['RuleNumber']})이 존재")

            has_issues = len(vulnerable_nacls) > 0
            risk_level = self.calculate_risk_level(len(vulnerable_nacls))
            
            return {
                'status': 'success',
                'has_issues': has_issues,
                'risk_level': risk_level,
                'message': f"모든 트래픽을 허용하는 광범위한 NACL 규칙 {len(vulnerable_nacls)}건 발견" if has_issues else "모든 트래픽을 허용하는 광범위한 NACL 규칙이 없습니다",
                'vulnerable_nacls': vulnerable_nacls,
                'summary': f"총 {len(vulnerable_nacls)}개의 위험한 네트워크 ACL 규칙이 발견되었습니다." if has_issues else "모든 네트워크 ACL 규칙이 안전합니다.",
                'details': {
                    'total_vulnerable_rules': len(vulnerable_nacls),
                    'inbound_rules': len([r for r in vulnerable_nacls if r['Direction'] == '인바운드']),
                    'outbound_rules': len([r for r in vulnerable_nacls if r['Direction'] == '아웃바운드'])
                }
            }

        except ClientError as e:
            print(f"[ERROR] 네트워크 ACL 정보를 가져오는 중 오류 발생: {e}")
            return {
                'status': 'error',
                'error_message': f"네트워크 ACL 정보를 가져오는 중 오류 발생: {str(e)}"
            }

    def execute_fix(self, selected_items):
        """
        [3.3] 네트워크 ACL 트래픽 정책 관리 조치
        - 사용자 확인 후 광범위한 허용 규칙을 삭제
        """
        if not selected_items:
            return [{'item': 'no_selection', 'status': 'info', 'message': '선택된 항목이 없습니다.'}]

        # 진단 재실행으로 최신 데이터 확보
        diagnosis_result = self.run_diagnosis()
        if diagnosis_result['status'] != 'success' or not diagnosis_result.get('vulnerable_nacls'):
            return [{'item': 'no_action_needed', 'status': 'info', 'message': '조치할 위험한 NACL 규칙이 없습니다.'}]

        vulnerable_nacls = diagnosis_result['vulnerable_nacls']
        ec2 = self.session.client('ec2')
        results = []
        
        print("[FIX] 3.3 광범위한 NACL 규칙에 대한 조치를 시작합니다.")
        
        for nacl_info in vulnerable_nacls:
            rule_id = f"{nacl_info['NaclId']}_{nacl_info['RuleNumber']}"
            
            # 선택된 항목인지 확인
            if any(rule_id in str(item) for item in selected_items.values() for item in item):
                try:
                    ec2.delete_network_acl_entry(
                        NetworkAclId=nacl_info['NaclId'],
                        RuleNumber=nacl_info['RuleNumber'],
                        Egress=nacl_info['Egress']
                    )
                    
                    print(f"     [SUCCESS] 규칙 #{nacl_info['RuleNumber']}을(를) 삭제했습니다.")
                    results.append({
                        'item': f"NACL {nacl_info['NaclId']}",
                        'status': 'success',
                        'message': f"NACL '{nacl_info['NaclId']}'의 위험한 규칙을 삭제했습니다."
                    })
                    
                except ClientError as e:
                    print(f"     [ERROR] 규칙 삭제 실패: {e}")
                    results.append({
                        'item': f"NACL {nacl_info['NaclId']}",
                        'status': 'error',
                        'message': f"NACL '{nacl_info['NaclId']}' 규칙 삭제 실패: {str(e)}"
                    })
            else:
                print(f"     [INFO] NACL '{nacl_info['NaclId']}'의 규칙 삭제를 건너뜁니다.")

        # 다른 체커들과 일관된 형식으로 results 배열 직접 반환
        return results

    def _get_fix_options(self, diagnosis_result):
        """자동 조치 옵션 반환"""
        if not diagnosis_result.get('vulnerable_nacls'):
            return []
            
        vulnerable_nacls = diagnosis_result['vulnerable_nacls']
        
        return [{
            'id': 'remove_broad_nacl_rules',
            'title': '광범위한 NACL 규칙 삭제',
            'description': '모든 트래픽을 허용하는 광범위한 네트워크 ACL 규칙을 삭제합니다.',
            'items': [
                {
                    'id': f"{nacl['NaclId']}_{nacl['RuleNumber']}",
                    'name': f"NACL {nacl['NaclId']}",
                    'description': f"규칙 #{nacl['RuleNumber']} ({nacl['Direction']}) - 모든 트래픽 허용"
                }
                for nacl in vulnerable_nacls
            ]
        }]