"""
3.1 보안 그룹 인/아웃바운드 ANY 설정 관리 진단
"""
import boto3
from ..base_checker import BaseChecker
import streamlit as st
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
        - 인바운드 및 아웃바운드 규칙에서 모든 IP(0.0.0.0/0, ::/0)에 대해 모든 포트가 열려 있는지 점검
        """
        try:
            if self.session:
                ec2 = self.session.client('ec2')
            else:
                ec2 = boto3.client('ec2')
            
            vulnerable_rules = []
            
            # 모든 보안 그룹 조회
            for sg in ec2.describe_security_groups()['SecurityGroups']:
                # Ingress (Inbound) 규칙 점검
                for rule in sg.get('IpPermissions', []):
                    vulnerable_rules.extend(self._check_rule(sg, rule, direction='ingress'))
                
                # Egress (Outbound) 규칙 점검  
                for rule in sg.get('IpPermissionsEgress', []):
                    vulnerable_rules.extend(self._check_rule(sg, rule, direction='egress'))

            # 위험도 계산
            finding_count = len(vulnerable_rules)
            risk_level = self.calculate_risk_level(
                finding_count,
                3 if finding_count > 3 else 2 if finding_count > 0 else 1
            )

            return {
                "status": "success",
                "vulnerable_rules": vulnerable_rules,
                "finding_count": finding_count,
                "affected_sgs": list(set([rule['GroupId'] for rule in vulnerable_rules])),
                "risk_level": risk_level,
                "has_issues": finding_count > 0
            }

        except ClientError as e:
            return {
                "status": "error",
                "error_message": f"보안 그룹 정보를 가져오는 중 오류 발생: {str(e)}"
            }
    
    def render_result_ui(self, result, item_key, ui_handler):
        """3.1 진단 결과 UI 렌더링"""
        col1, col2 = st.columns(2)
        with col1:
            st.metric("위험한 ANY 규칙", result.get('finding_count', 0))
        with col2:
            affected_sgs = result.get('affected_sgs', [])
            st.metric("영향받는 보안그룹", len(affected_sgs))
        
        # 발견된 문제 표시
        if result.get('vulnerable_rules'):
            with st.expander("🔍 ANY 포트가 열려있는 보안 그룹 규칙"):
                for rule in result['vulnerable_rules']:
                    direction_icon = "⬇️" if rule['Direction'] == 'ingress' else "⬆️"
                    protocol_info = f"{rule['Protocol']}" if rule['Protocol'] != '-1' else "All Protocols"
                    port_info = f"Port {rule['FromPort']}-{rule['ToPort']}" if rule['FromPort'] != 'all' else "All Ports"
                    
                    st.write(f"{direction_icon} **[{rule['Direction'].upper()}]** `{rule['GroupId']}` ({rule['GroupName']})")
                    st.write(f"   └─ **소스:** `{rule['Source']}` → **{protocol_info}** ({port_info})")
        
        # 조치 안내
        if result.get('has_issues', False):
            st.error("🚨 **위험**: 모든 IP에서 모든 포트로의 접근이 허용되고 있습니다!")
            st.warning("⚠️ 이는 심각한 보안 위험을 초래할 수 있습니다.")
            
            if st.button("🔧 즉시 조치", key=f"fix_{item_key}"):
                st.session_state[f'show_fix_{item_key}'] = True
                st.rerun()
            
            if st.session_state.get(f'show_fix_{item_key}', False):
                ui_handler.show_fix_form(result, item_key, self.item_code)
        else:
            st.success("✅ ANY 포트가 열려 있는 인/아웃바운드 규칙이 없습니다.")
        
        # 재진단 버튼
        ui_handler.show_rediagnose_button(item_key)
    
    def render_fix_form(self, result, item_key, ui_handler):
        """3.1 조치 폼 UI 렌더링"""
        with st.form(f"fix_form_31_{item_key}"):
            st.markdown("**🔧 위험한 보안 그룹 규칙 조치**")
            st.warning("⚠️ 선택된 규칙들이 자동으로 제거됩니다. 신중하게 선택하세요.")
            
            st.markdown("**조치할 규칙을 선택하세요:**")
            
            selected_rules = []
            for i, rule in enumerate(result.get('vulnerable_rules', [])):
                direction_icon = "⬇️" if rule['Direction'] == 'ingress' else "⬆️"
                protocol_info = f"{rule['Protocol']}" if rule['Protocol'] != '-1' else "All Protocols"
                port_info = f"Port {rule['FromPort']}-{rule['ToPort']}" if rule['FromPort'] != 'all' else "All Ports"
                
                rule_description = f"{direction_icon} [{rule['Direction'].upper()}] {rule['GroupId']} → {rule['Source']} ({protocol_info}, {port_info})"
                
                if st.checkbox(rule_description, key=f"rule_31_{i}_{item_key}"):
                    selected_rules.append(rule)
            
            col_submit1, col_submit2 = st.columns(2)
            with col_submit1:
                if st.form_submit_button("🛡️ 선택된 규칙 제거", type="primary"):
                    if selected_rules:
                        fix_results = self.execute_fix({'selected_rules': selected_rules})
                        ui_handler._show_fix_results(fix_results)
                        st.success("✅ 보안 그룹 규칙 조치가 완료되었습니다!")
                        st.session_state[f'show_fix_{item_key}'] = False
                        st.session_state[f'fix_completed_{item_key}'] = True
                        st.rerun()
                    else:
                        st.warning("조치할 규칙을 선택해주세요.")
            
            with col_submit2:
                if st.form_submit_button("❌ 취소"):
                    st.session_state[f'show_fix_{item_key}'] = False
                    st.rerun()
    
    def execute_fix(self, selected_items):
        """조치 실행 (BaseChecker 추상 메서드 구현)"""
        if not selected_items.get('selected_rules'):
            return [{"user": "보안 그룹", "action": "규칙 제거", "status": "error", "error": "선택된 규칙이 없습니다."}]
        
        try:
            if self.session:
                ec2 = self.session.client('ec2')
            else:
                ec2 = boto3.client('ec2')
            
            results = []
            
            for rule_detail in selected_items['selected_rules']:
                try:
                    # IP Permission 구성
                    ip_permission = {
                        'IpProtocol': rule_detail['Rule']['IpProtocol']
                    }
                    
                    # IPv4 또는 IPv6 범위 설정
                    if '0.0.0.0/0' in rule_detail['Source']:
                        ip_permission['IpRanges'] = [{'CidrIp': '0.0.0.0/0'}]
                    elif '::/0' in rule_detail['Source']:
                        ip_permission['Ipv6Ranges'] = [{'CidrIpv6': '::/0'}]
                    
                    # 포트 정보 추가 (프로토콜이 -1이 아닌 경우)
                    if rule_detail['Rule']['IpProtocol'] != '-1':
                        if 'FromPort' in rule_detail['Rule']:
                            ip_permission['FromPort'] = rule_detail['Rule']['FromPort']
                        if 'ToPort' in rule_detail['Rule']:
                            ip_permission['ToPort'] = rule_detail['Rule']['ToPort']
                    
                    # 규칙 제거 실행
                    if rule_detail['Direction'] == 'ingress':
                        ec2.revoke_security_group_ingress(
                            GroupId=rule_detail['GroupId'],
                            IpPermissions=[ip_permission]
                        )
                    else:
                        ec2.revoke_security_group_egress(
                            GroupId=rule_detail['GroupId'],
                            IpPermissions=[ip_permission]
                        )
                    
                    results.append({
                        "user": f"SG {rule_detail['GroupId']}",
                        "action": f"{rule_detail['Direction']} 규칙 제거 ({rule_detail['Source']})",
                        "status": "success"
                    })
                    
                except ClientError as e:
                    results.append({
                        "user": f"SG {rule_detail['GroupId']}",
                        "action": f"{rule_detail['Direction']} 규칙 제거",
                        "status": "error",
                        "error": str(e)
                    })
            
            return results
            
        except Exception as e:
            return [{
                "user": "보안 그룹",
                "action": "규칙 제거",
                "status": "error",
                "error": str(e)
            }]