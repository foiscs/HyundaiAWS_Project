"""
3.2 보안 그룹 인/아웃바운드 불필요 정책 관리 진단
"""
import boto3
from ..base_checker import BaseChecker
import streamlit as st
from botocore.exceptions import ClientError

class SecurityGroupUnnecessaryChecker(BaseChecker):
    """3.2 보안 그룹 인/아웃바운드 불필요 정책 관리 진단"""
    
    @property
    def item_code(self):
        return "3.2"
    
    @property 
    def item_name(self):
        return "보안 그룹 인/아웃바운드 불필요 정책 관리"
    
    def is_sg_in_use(self, ec2, sg_id):
        """보안 그룹이 사용 중인지 확인"""
        # 1. ENI 확인
        try:
            eni = ec2.describe_network_interfaces(Filters=[{'Name': 'group-id', 'Values': [sg_id]}])
            if eni['NetworkInterfaces']:
                return True, "ENI"
        except ClientError:
            pass

        # 2. EC2 인스턴스 확인
        try:
            ec2s = ec2.describe_instances(Filters=[{'Name': 'instance.group-id', 'Values': [sg_id]}])
            for reservation in ec2s.get('Reservations', []):
                if reservation['Instances']:
                    return True, "EC2"
        except ClientError:
            pass

        # 3. RDS 확인
        try:
            if self.session:
                rds = self.session.client('rds')
            else:
                rds = boto3.client('rds')
            rds_instances = rds.describe_db_instances()
            for db in rds_instances['DBInstances']:
                if any(sg['VpcSecurityGroupId'] == sg_id for sg in db.get('VpcSecurityGroups', [])):
                    return True, "RDS"
        except ClientError:
            pass

        # 4. ELB 확인
        try:
            if self.session:
                elb = self.session.client('elbv2')
            else:
                elb = boto3.client('elbv2')
            elbs = elb.describe_load_balancers()
            for lb in elbs['LoadBalancers']:
                if sg_id in lb.get('SecurityGroups', []):
                    return True, "ELB"
        except ClientError:
            pass

        # 5. Lambda 확인
        try:
            if self.session:
                lam = self.session.client('lambda')
            else:
                lam = boto3.client('lambda')
            funcs = lam.list_functions()['Functions']
            for fn in funcs:
                cfg = lam.get_function_configuration(FunctionName=fn['FunctionName'])
                if sg_id in cfg.get('VpcConfig', {}).get('SecurityGroupIds', []):
                    return True, "Lambda"
        except ClientError:
            pass

        return False, None

    def can_delete_sg(self, ec2, sg_id):
        """보안 그룹을 삭제할 수 있는지 확인 (더 정확한 검증)"""
        try:
            # 다른 보안 그룹에서 이 보안 그룹을 참조하는지 확인
            all_sgs = ec2.describe_security_groups()['SecurityGroups']
            for sg in all_sgs:
                if sg['GroupId'] == sg_id:
                    continue
                
                # 인바운드 규칙에서 참조 확인
                for rule in sg.get('IpPermissions', []):
                    for source_sg in rule.get('UserIdGroupPairs', []):
                        if source_sg.get('GroupId') == sg_id:
                            return False
                
                # 아웃바운드 규칙에서 참조 확인  
                for rule in sg.get('IpPermissionsEgress', []):
                    for source_sg in rule.get('UserIdGroupPairs', []):
                        if source_sg.get('GroupId') == sg_id:
                            return False
            
            return True
            
        except ClientError as e:
            return False
    
    def run_diagnosis(self):
        """
        진단 수행
        - ANY IP 규칙을 포함하면서 사용되지 않는 보안 그룹을 찾아 삭제 가능한 대상을 반환
        """
        try:
            if self.session:
                ec2 = self.session.client('ec2')
            else:
                ec2 = boto3.client('ec2')
            
            deletable_sgs = []
            
            all_sgs = ec2.describe_security_groups()['SecurityGroups']
            
            for sg in all_sgs:
                sg_id = sg['GroupId']
                sg_name = sg.get('GroupName', 'N/A')
                
                # ANY IP 규칙 포함 여부 확인
                has_any_ip = any(
                    any(ip.get('CidrIp') == '0.0.0.0/0' for ip in rule.get('IpRanges', [])) or
                    any(ip.get('CidrIpv6') == '::/0' for ip in rule.get('Ipv6Ranges', []))
                    for rule in sg.get('IpPermissions', []) + sg.get('IpPermissionsEgress', [])
                )
                
                if not has_any_ip:
                    continue
                
                # 기본 보안 그룹은 제외
                if sg_name == 'default':
                    continue
                
                # 사용 중인 보안 그룹은 제외
                in_use, used_by = self.is_sg_in_use(ec2, sg_id)
                if in_use:
                    continue
                
                # 삭제 가능한지 확인
                if not self.can_delete_sg(ec2, sg_id):
                    continue
                
                deletable_sgs.append({
                    'GroupId': sg_id,
                    'GroupName': sg_name,
                    'Description': sg.get('Description', ''),
                    'VpcId': sg.get('VpcId', ''),
                    'RuleCount': len(sg.get('IpPermissions', [])) + len(sg.get('IpPermissionsEgress', []))
                })

            # 위험도 계산
            finding_count = len(deletable_sgs)
            risk_level = self.calculate_risk_level(
                finding_count,
                2 if finding_count > 2 else 1 if finding_count > 0 else 1
            )

            return {
                "status": "success",
                "deletable_sgs": deletable_sgs,
                "finding_count": finding_count,
                "risk_level": risk_level,
                "has_issues": finding_count > 0
            }

        except ClientError as e:
            return {
                "status": "error",
                "error_message": f"보안 그룹 점검 중 오류 발생: {str(e)}"
            }
    
    def render_result_ui(self, result, item_key, ui_handler):
        """3.2 진단 결과 UI 렌더링"""
        st.metric("삭제 가능한 보안그룹", result.get('finding_count', 0))
        
        # 발견된 문제 표시
        if result.get('deletable_sgs'):
            with st.expander("🔍 삭제 가능한 불필요 보안 그룹 목록"):
                for sg in result['deletable_sgs']:
                    st.write(f"🗑️ **{sg['GroupId']}** ({sg['GroupName']})")
                    st.write(f"   └─ **설명:** {sg['Description']}")
                    st.write(f"   └─ **VPC:** {sg['VpcId']} | **규칙 수:** {sg['RuleCount']}개")
                    st.write("")
        
        # 조치 안내
        if result.get('has_issues', False):
            st.warning("⚠️ ANY IP 규칙을 포함하면서 사용되지 않는 보안 그룹이 발견되었습니다.")
            st.info("💡 이러한 보안 그룹은 보안 위험을 줄이기 위해 삭제하는 것이 좋습니다.")
            
            if st.button("🔧 즉시 조치", key=f"fix_{item_key}"):
                st.session_state[f'show_fix_{item_key}'] = True
                st.rerun()
            
            if st.session_state.get(f'show_fix_{item_key}', False):
                ui_handler.show_fix_form(result, item_key, self.item_code)
        else:
            st.success("✅ 삭제 가능한 불필요한 보안 그룹이 없습니다.")
        
        # 재진단 버튼
        ui_handler.show_rediagnose_button(item_key)
    
    def render_fix_form(self, result, item_key, ui_handler):
        """3.2 조치 폼 UI 렌더링"""
        with st.form(f"fix_form_32_{item_key}"):
            st.markdown("**🔧 불필요한 보안 그룹 삭제**")
            st.warning("⚠️ 선택된 보안 그룹들이 영구적으로 삭제됩니다. 신중하게 선택하세요.")
            
            st.markdown("**삭제할 보안 그룹을 선택하세요:**")
            
            selected_sgs = []
            for i, sg in enumerate(result.get('deletable_sgs', [])):
                sg_description = f"🗑️ {sg['GroupId']} ({sg['GroupName']}) - {sg['Description']}"
                
                if st.checkbox(sg_description, key=f"sg_32_{i}_{item_key}"):
                    selected_sgs.append(sg)
            
            col_submit1, col_submit2 = st.columns(2)
            with col_submit1:
                if st.form_submit_button("🗑️ 선택된 보안그룹 삭제", type="primary"):
                    if selected_sgs:
                        fix_results = self.execute_fix({'selected_sgs': selected_sgs})
                        ui_handler._show_fix_results(fix_results)
                        st.success("✅ 보안 그룹 삭제 조치가 완료되었습니다!")
                        st.session_state[f'show_fix_{item_key}'] = False
                        st.session_state[f'fix_completed_{item_key}'] = True
                        st.rerun()
                    else:
                        st.warning("삭제할 보안 그룹을 선택해주세요.")
            
            with col_submit2:
                if st.form_submit_button("❌ 취소"):
                    st.session_state[f'show_fix_{item_key}'] = False
                    st.rerun()
    
    def execute_fix(self, selected_items):
        """조치 실행 (BaseChecker 추상 메서드 구현)"""
        if not selected_items.get('selected_sgs'):
            return [{"user": "보안 그룹", "action": "삭제", "status": "error", "error": "선택된 보안 그룹이 없습니다."}]
        
        try:
            if self.session:
                ec2 = self.session.client('ec2')
            else:
                ec2 = boto3.client('ec2')
            
            results = []
            
            for sg in selected_items['selected_sgs']:
                try:
                    # 삭제 전 마지막 확인
                    in_use, used_by = self.is_sg_in_use(ec2, sg['GroupId'])
                    if in_use:
                        results.append({
                            "user": f"SG {sg['GroupId']}",
                            "action": f"보안 그룹 삭제",
                            "status": "error",
                            "error": f"현재 {used_by}에서 사용 중이어서 삭제할 수 없습니다."
                        })
                        continue
                    
                    # 실제 삭제 실행
                    ec2.delete_security_group(GroupId=sg['GroupId'])
                    
                    results.append({
                        "user": f"SG {sg['GroupId']}",
                        "action": f"보안 그룹 삭제 ({sg['GroupName']})",
                        "status": "success"
                    })
                    
                except ClientError as e:
                    error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                    error_message = e.response.get('Error', {}).get('Message', str(e))
                    
                    results.append({
                        "user": f"SG {sg['GroupId']}",
                        "action": f"보안 그룹 삭제",
                        "status": "error",
                        "error": f"[{error_code}] {error_message}"
                    })
            
            return results
            
        except Exception as e:
            return [{
                "user": "보안 그룹",
                "action": "삭제",
                "status": "error",
                "error": str(e)
            }]