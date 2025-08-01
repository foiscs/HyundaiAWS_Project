"""
[3.1] 보안 그룹 인/아웃바운드 ANY 설정 관리 체커
원본: SHIELDUS-AWS-CHECKER/virtual_resources/3_1_sg_any_rule.py
"""

import boto3
from botocore.exceptions import ClientError
from app.checkers.base_checker import BaseChecker


class SecurityGroupAnyRuleChecker(BaseChecker):
    """[3.1] 보안 그룹 인/아웃바운드 ANY 설정 관리 체커"""
    
    @property
    def item_code(self):
        return "3.1"
    
    @property 
    def item_name(self):
        return "보안 그룹 인/아웃바운드 ANY 설정 관리"
    
    def run_diagnosis(self):
        """
        [3.1] 보안 그룹 인/아웃바운드 ANY 설정 관리
        - 인바운드 및 아웃바운드 규칙에서 모든 IP(0.0.0.0/0, ::/0)에 대해 모든 포트가 열려 있는지 점검
        """
        print("[INFO] 3.1 보안 그룹 인/아웃바운드 ANY 설정 관리 체크 중...")
        
        try:
            if self.session:
                ec2 = self.session.client('ec2')
            else:
                ec2 = self.session.client('ec2')
                
            vulnerable_rules = []

            for sg in ec2.describe_security_groups()['SecurityGroups']:
                # Ingress (Inbound)
                for rule in sg.get('IpPermissions', []):
                    vulnerable_rules.extend(self._check_rule(sg, rule, direction='ingress'))
                # Egress (Outbound)
                for rule in sg.get('IpPermissionsEgress', []):
                    vulnerable_rules.extend(self._check_rule(sg, rule, direction='egress'))

            if not vulnerable_rules:
                print("[✓ COMPLIANT] 3.1 ANY 포트가 열려 있는 인/아웃바운드 규칙이 없습니다.")
            else:
                print(f"[⚠ WARNING] 3.1 ANY 포트가 열려 있는 규칙이 존재합니다 ({len(vulnerable_rules)}건).")
                for finding in vulnerable_rules:
                    print(f"  ├─ [{finding['Direction'].upper()}] SG '{finding['GroupId']}' ({finding['GroupName']}): 소스 {finding['Source']}에 전체 포트 허용")

            # 결과 분석
            has_issues = len(vulnerable_rules) > 0
            risk_level = self.calculate_risk_level(len(vulnerable_rules))
            
            return {
                'status': 'success',
                'has_issues': has_issues,
                'risk_level': risk_level,
                'total_vulnerable_rules': len(vulnerable_rules),
                'vulnerable_rules': vulnerable_rules,
                'ingress_rules_count': len([r for r in vulnerable_rules if r['Direction'] == 'ingress']),
                'egress_rules_count': len([r for r in vulnerable_rules if r['Direction'] == 'egress']),
                'recommendation': "보안 그룹에서 0.0.0.0/0 또는 ::/0으로 모든 포트를 허용하는 규칙은 보안 위험을 초래할 수 있습니다. 필요한 포트와 IP 범위만 허용하도록 수정하세요."
            }

        except ClientError as e:
            return {
                'status': 'error',
                'error_message': f'보안 그룹 정보를 가져오는 중 오류 발생: {str(e)}'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error_message': f'진단 수행 중 예상치 못한 오류가 발생했습니다: {str(e)}'
            }

    def _check_rule(self, sg, rule, direction='ingress'):
        """보안 그룹 규칙 점검 - 원본 _check_rule 함수"""
        findings = []
        if rule.get('IpProtocol') == '-1' or (
            rule.get('FromPort') == 0 and rule.get('ToPort') == 65535
        ):
            for ip_range in rule.get('IpRanges', []):
                if ip_range.get('CidrIp') == '0.0.0.0/0':
                    findings.append({
                        'GroupId': sg['GroupId'],
                        'GroupName': sg['GroupName'],
                        'Source': '0.0.0.0/0',
                        'Rule': rule,
                        'Direction': direction
                    })
            for ipv6_range in rule.get('Ipv6Ranges', []):
                if ipv6_range.get('CidrIpv6') == '::/0':
                    findings.append({
                        'GroupId': sg['GroupId'],
                        'GroupName': sg['GroupName'],
                        'Source': '::/0',
                        'Rule': rule,
                        'Direction': direction
                    })
        return findings
    
    def _format_result_summary(self, result):
        """결과 요약 포맷팅"""
        if result.get('has_issues'):
            vulnerable_count = result.get('total_vulnerable_rules', 0)
            return f"⚠️ ANY 포트가 열려 있는 보안 그룹 규칙 {vulnerable_count}건이 발견되었습니다."
        else:
            return f"✅ ANY 포트가 열려 있는 보안 그룹 규칙이 없습니다."
    
    def _format_result_details(self, result):
        """결과 상세 정보 포맷팅"""
        details = {
            'total_vulnerable_rules': {
                'count': result.get('total_vulnerable_rules', 0),
                'description': '전체 위험한 보안 그룹 규칙 수'
            },
            'ingress_rules': {
                'count': result.get('ingress_rules_count', 0),
                'description': '위험한 인바운드 규칙 수'
            },
            'egress_rules': {
                'count': result.get('egress_rules_count', 0),
                'description': '위험한 아웃바운드 규칙 수'
            }
        }
        
        if result.get('has_issues'):
            vulnerable_rules = result.get('vulnerable_rules', [])
            details['vulnerable_rules_details'] = {
                'count': len(vulnerable_rules),
                'rules': [{
                    'group_id': rule['GroupId'],
                    'group_name': rule['GroupName'],  
                    'direction': rule['Direction'],
                    'source': rule['Source'],
                    'protocol': rule['Rule'].get('IpProtocol', 'unknown')
                } for rule in vulnerable_rules],
                'description': '위험한 보안 그룹 규칙 상세 정보',
                'recommendation': result.get('recommendation', '')
            }
        
        return details
    
    def _get_fix_options(self, result):
        """자동 조치 옵션 반환"""
        if not result.get('has_issues'):
            return []
        
        vulnerable_rules = result.get('vulnerable_rules', [])
        if not vulnerable_rules:
            return []
        
        return [{
            'id': 'remove_any_rules',
            'title': '위험한 보안 그룹 규칙 제거',
            'description': 'ANY 포트가 열려있는 위험한 보안 그룹 규칙을 제거합니다.',
            'items': [
                {
                    'id': f"{rule['GroupId']}_{rule['Direction']}_{rule['Source']}",
                    'name': f"SG {rule['GroupId']} ({rule['GroupName']})",
                    'description': f"{rule['Direction'].upper()} 규칙: {rule['Source']} -> 전체 포트"
                }
                for rule in vulnerable_rules
            ]
        }]
    
    def execute_fix(self, selected_items):
        """
        [3.1] 보안 그룹 ANY 설정 관리 조치
        - 사용자 확인 후 위험한 인바운드/아웃바운드 규칙을 제거
        """
        if not selected_items:
            return [{
                'item': 'no_selection',
                'status': 'info',
                'message': '선택된 항목이 없습니다.'
            }]

        # 진단 재실행으로 최신 데이터 확보
        diagnosis_result = self.run_diagnosis()
        if diagnosis_result['status'] != 'success' or not diagnosis_result.get('vulnerable_rules'):
            return [{
                'item': 'no_action_needed',
                'status': 'info',
                'message': '조치할 위험한 규칙이 없습니다.'
            }]

        vulnerable_rules_details = diagnosis_result['vulnerable_rules']
        
        try:
            if self.session:
                ec2 = self.session.client('ec2')
            else:
                ec2 = self.session.client('ec2')
        except Exception as e:
            return [{
                'item': 'connection_error',
                'status': 'error',
                'message': f'AWS 연결 실패: {str(e)}'
            }]
        
        results = []
        print("[FIX] 3.1 보안 그룹 ANY 포트 규칙에 대한 조치를 시작합니다.")
        
        for detail in vulnerable_rules_details:
            rule_id = f"{detail['GroupId']}_{detail['Direction']}_{detail['Source']}"
            
            # 선택된 항목인지 확인
            if any(rule_id in str(item) for item_list in selected_items.values() for item in item_list):
                direction = detail['Direction']
                
                try:
                    # 원본 fix 함수의 로직 그대로 구현
                    ip_permission = {
                        'IpProtocol': detail['Rule']['IpProtocol'],
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}] if '0.0.0.0/0' in detail['Source'] else [],
                        'Ipv6Ranges': [{'CidrIpv6': '::/0'}] if '::/0' in detail['Source'] else []
                    }

                    if detail['Rule']['IpProtocol'] != '-1':
                        ip_permission['FromPort'] = detail['Rule'].get('FromPort')
                        ip_permission['ToPort'] = detail['Rule'].get('ToPort')

                    revoke_func = ec2.revoke_security_group_ingress if direction == 'ingress' else ec2.revoke_security_group_egress
                    revoke_func(GroupId=detail['GroupId'], IpPermissions=[ip_permission])
                    
                    print(f"     [SUCCESS] SG '{detail['GroupId']}'에서 해당 규칙을 제거했습니다.")
                    results.append({
                        'item': f"SG {detail['GroupId']}",
                        'status': 'success',
                        'message': f"SG '{detail['GroupId']}'에서 위험한 {direction} 규칙({detail['Source']} -> 전체 포트)을 제거했습니다."
                    })
                    
                except ClientError as e:
                    print(f"     [ERROR] 규칙 제거 실패: {e}")
                    results.append({
                        'item': f"SG {detail['GroupId']}",
                        'status': 'error',
                        'message': f"SG '{detail['GroupId']}' 규칙 제거 실패: {str(e)}"
                    })
            else:
                print(f"     [INFO] SG '{detail['GroupId']}'의 규칙 제거를 건너뜁니다.")

        return results