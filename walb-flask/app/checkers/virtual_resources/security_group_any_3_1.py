"""
3.1 보안 그룹 인/아웃바운드 ANY 설정 관리 진단 (Flask용)
mainHub의 security_group_any_3_1.py를 Streamlit 종속성 제거하여 이식
"""
import boto3
from ..base_checker import BaseChecker
from botocore.exceptions import ClientError

class SecurityGroupAnyChecker(BaseChecker):
    """3.1 보안 그룹 인/아웃바운드 ANY 설정 관리 진단"""
    
    @property
    def item_code(self):
        return "3.1"
    
    @property 
    def item_name(self):
        return "보안 그룹 인/아웃바운드 ANY 설정 관리"
    
    def _check_rule(self, sg, rule, direction='ingress'):
        """규칙 점검 - 모든 IP에 대해 모든 포트가 열려있는지 확인"""
        findings = []
        
        # 모든 프로토콜(-1) 또는 모든 포트(0-65535) 확인
        if rule.get('IpProtocol') == '-1' or (
            rule.get('FromPort') == 0 and rule.get('ToPort') == 65535
        ):
            # IPv4 0.0.0.0/0 확인
            for ip_range in rule.get('IpRanges', []):
                if ip_range.get('CidrIp') == '0.0.0.0/0':
                    findings.append({
                        'GroupId': sg['GroupId'],
                        'GroupName': sg['GroupName'],
                        'Source': '0.0.0.0/0',
                        'Rule': rule,
                        'Direction': direction,
                        'Protocol': rule.get('IpProtocol', 'all'),
                        'FromPort': rule.get('FromPort', 'all'),
                        'ToPort': rule.get('ToPort', 'all')
                    })
            
            # IPv6 ::/0 확인
            for ipv6_range in rule.get('Ipv6Ranges', []):
                if ipv6_range.get('CidrIpv6') == '::/0':
                    findings.append({
                        'GroupId': sg['GroupId'],
                        'GroupName': sg['GroupName'],
                        'Source': '::/0',
                        'Rule': rule,
                        'Direction': direction,
                        'Protocol': rule.get('IpProtocol', 'all'),
                        'FromPort': rule.get('FromPort', 'all'),
                        'ToPort': rule.get('ToPort', 'all')
                    })
        
        return findings
    
    def run_diagnosis(self):
        """
        진단 수행
        - 보안 그룹에서 0.0.0.0/0 또는 ::/0에 모든 포트가 열려있는 규칙 점검
        """
        try:
            if self.session:
                ec2 = self.session.client('ec2')
            else:
                ec2 = boto3.client('ec2')
            
            insecure_rules = []
            total_security_groups = 0
            
            # 모든 보안 그룹 조회
            paginator = ec2.get_paginator('describe_security_groups')
            for page in paginator.paginate():
                for sg in page['SecurityGroups']:
                    total_security_groups += 1
                    
                    # 인바운드 규칙 점검
                    for rule in sg.get('IpPermissions', []):
                        findings = self._check_rule(sg, rule, 'ingress')
                        insecure_rules.extend(findings)
                    
                    # 아웃바운드 규칙 점검
                    for rule in sg.get('IpPermissionsEgress', []):
                        findings = self._check_rule(sg, rule, 'egress')
                        insecure_rules.extend(findings)
            
            # 위험도 계산
            issues_count = len(insecure_rules)
            risk_level = self.calculate_risk_level(
                issues_count,
                3  # ANY 허용은 높은 위험도
            )
            
            return {
                "status": "success",
                "insecure_rules": insecure_rules,
                "total_security_groups": total_security_groups,
                "issues_count": issues_count,
                "risk_level": risk_level,
                "has_issues": issues_count > 0
            }

        except ClientError as e:
            return {
                "status": "error",
                "error_message": str(e)
            }
    
    def _format_result_summary(self, result):
        """결과 요약 포맷팅"""
        total_sgs = result.get('total_security_groups', 0)
        issues_count = result.get('issues_count', 0)
        
        if issues_count > 0:
            return f"⚠️ 전체 {total_sgs}개 보안 그룹에서 {issues_count}개의 ANY 허용 규칙이 발견되었습니다."
        else:
            return f"✅ 모든 {total_sgs}개 보안 그룹에서 ANY 허용 규칙이 발견되지 않았습니다."
    
    def _format_result_details(self, result):
        """결과 상세 정보 포맷팅"""
        details = {
            "보안 그룹 검사 결과": {
                "검사한 보안 그룹": result.get('total_security_groups', 0),
                "ANY 허용 규칙": result.get('issues_count', 0),
                "recommendation": "모든 IP(0.0.0.0/0, ::/0)에 대해 모든 포트를 열어두는 것은 보안 위험을 초래합니다."
            }
        }
        
        if result.get('insecure_rules'):
            details["위험한 보안 그룹 규칙"] = {}
            for rule in result['insecure_rules']:
                rule_key = f"{rule['GroupId']} ({rule['Direction']})"
                details["위험한 보안 그룹 규칙"][rule_key] = {
                    "그룹명": rule['GroupName'],
                    "방향": rule['Direction'],
                    "소스": rule['Source'],
                    "프로토콜": rule['Protocol'],
                    "포트 범위": f"{rule['FromPort']}-{rule['ToPort']}"
                }
        
        return details
    
    def _get_fix_options(self, result):
        """자동 조치 옵션 반환"""
        if not result.get('has_issues'):
            return None
        
        insecure_rules = result.get('insecure_rules', [])
        
        if insecure_rules:
            return [{
                "type": "remove_any_rules",
                "title": "ANY 허용 규칙 제거",
                "description": f"{len(insecure_rules)}개의 위험한 ANY 허용 규칙을 제거합니다.",
                "items": [{"group_id": rule['GroupId'], 
                          "group_name": rule['GroupName'],
                          "direction": rule['Direction'],
                          "source": rule['Source'],
                          "action": "ANY 규칙 제거"} 
                         for rule in insecure_rules],
                "severity": "high",
                "warning": "주의: 보안 그룹 규칙 제거는 서비스 접근에 영향을 줄 수 있습니다."
            }]
        
        return None
    
    def execute_fix(self, selected_items):
        """조치 실행"""
        try:
            if self.session:
                ec2 = self.session.client('ec2')
            else:
                ec2 = boto3.client('ec2')
            
            results = []
            rules_to_remove = selected_items.get('insecure_rules', [])
            
            for rule_info in rules_to_remove:
                try:
                    group_id = rule_info['GroupId']
                    direction = rule_info['Direction']
                    rule = rule_info['Rule']
                    
                    if direction == 'ingress':
                        ec2.revoke_security_group_ingress(
                            GroupId=group_id,
                            IpPermissions=[rule]
                        )
                    else:  # egress
                        ec2.revoke_security_group_egress(
                            GroupId=group_id,
                            IpPermissions=[rule]
                        )
                    
                    results.append({
                        "group_id": group_id,
                        "direction": direction,
                        "action": "ANY 규칙 제거",
                        "status": "success"
                    })
                except ClientError as e:
                    results.append({
                        "group_id": rule_info.get('GroupId', 'unknown'),
                        "direction": rule_info.get('Direction', 'unknown'),
                        "action": "ANY 규칙 제거",
                        "status": "error",
                        "error": str(e)
                    })
            
            return results
            
        except Exception as e:
            return [{
                "group_id": "전체",
                "action": "ANY 규칙 제거",
                "status": "error",
                "error": str(e)
            }]