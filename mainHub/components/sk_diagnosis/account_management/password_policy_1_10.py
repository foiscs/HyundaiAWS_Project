"""
1.10 AWS 계정 패스워드 정책 관리 진단
"""
import boto3
from ..base_checker import BaseChecker
import streamlit as st
from botocore.exceptions import ClientError

class PasswordPolicyChecker(BaseChecker):
    """1.10 AWS 계정 패스워드 정책 관리 진단"""
    
    @property
    def item_code(self):
        return "1.10"
    
    @property 
    def item_name(self):
        return "AWS 계정 패스워드 정책 관리"
    
    def run_diagnosis(self):
        """
        진단 수행
        - 계정의 패스워드 정책이 권장 기준을 충족하는지 점검
        """
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = boto3.client('iam')
            
            findings = []
            is_non_compliant = False
            policy_exists = False
            current_policy = {}

            try:
                policy_response = iam.get_account_password_policy()
                policy = policy_response['PasswordPolicy']
                policy_exists = True
                current_policy = policy
                
                # 최소 길이 검사 (8자 이상)
                if policy.get('MinimumPasswordLength', 0) < 8:
                    findings.append("최소 길이 8자 미만")
                    is_non_compliant = True
                
                # 복잡도 검사 (3종류 이상)
                complexity_count = sum([
                    1 for k in ['RequireSymbols', 'RequireNumbers', 
                               'RequireUppercaseCharacters', 'RequireLowercaseCharacters'] 
                    if policy.get(k, False)
                ])
                if complexity_count < 3:
                    findings.append("복잡도 3종류 미만")
                    is_non_compliant = True
                
                # 재사용 방지 검사
                if not policy.get('PasswordReusePrevention'):
                    findings.append("재사용 방지 미설정")
                    is_non_compliant = True
                
                # 만료 기간 검사 (90일 이하)
                if not policy.get('ExpirePasswords') or policy.get('MaxPasswordAge', 1000) > 90:
                    findings.append("만료 기간 90일 초과 또는 미설정")
                    is_non_compliant = True

            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchEntity':
                    is_non_compliant = True
                    findings.append("패스워드 정책이 설정되지 않음")
                else:
                    return {
                        "status": "error",
                        "error_message": f"패스워드 정책 정보를 가져오는 중 오류 발생: {str(e)}"
                    }

            # 위험도 계산
            finding_count = len(findings)
            risk_level = self.calculate_risk_level(
                finding_count,
                2 if finding_count > 2 else 1
            )

            return {
                "status": "success",
                "policy_exists": policy_exists,
                "current_policy": current_policy,
                "findings": findings,
                "finding_count": finding_count,
                "is_non_compliant": is_non_compliant,
                "risk_level": risk_level,
                "has_issues": is_non_compliant
            }

        except ClientError as e:
            return {
                "status": "error",
                "error_message": str(e)
            }
    
    def render_result_ui(self, result, item_key, ui_handler):
        """1.10 진단 결과 UI 렌더링"""
        st.info("ℹ️ Admin Console의 패스워드 복잡성 정책은 AWS 내부 정책에 의해 관리되며, IAM 정책만 점검할 수 있습니다.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("정책 설정 여부", "✅ 설정됨" if result.get('policy_exists') else "❌ 미설정")
        with col2:
            st.metric("발견된 문제", result.get('finding_count', 0))
        
        # 현재 정책 상태 표시
        if result.get('policy_exists') and result.get('current_policy'):
            with st.expander("현재 패스워드 정책 상세 정보"):
                policy = result['current_policy']
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write(f"**최소 길이:** {policy.get('MinimumPasswordLength', 'N/A')}자")
                    st.write(f"**대문자 필요:** {'✅' if policy.get('RequireUppercaseCharacters') else '❌'}")
                    st.write(f"**소문자 필요:** {'✅' if policy.get('RequireLowercaseCharacters') else '❌'}")
                with col_b:
                    st.write(f"**숫자 필요:** {'✅' if policy.get('RequireNumbers') else '❌'}")
                    st.write(f"**특수문자 필요:** {'✅' if policy.get('RequireSymbols') else '❌'}")
                    st.write(f"**최대 사용기간:** {policy.get('MaxPasswordAge', 'N/A')}일")
                
                st.write(f"**재사용 방지:** {policy.get('PasswordReusePrevention', 0)}개 이전 패스워드")
                st.write(f"**만료 활성화:** {'✅' if policy.get('ExpirePasswords') else '❌'}")
        
        # 발견된 문제 표시
        if result.get('findings'):
            with st.expander("🔍 발견된 문제점 보기"):
                for finding in result['findings']:
                    st.write(f"• {finding}")
        
        # 조치 버튼
        if result.get('has_issues', False):
            if st.button("🔧 즉시 조치", key=f"fix_{item_key}"):
                st.session_state[f'show_fix_{item_key}'] = True
                st.rerun()
            
            if st.session_state.get(f'show_fix_{item_key}', False):
                ui_handler.show_fix_form(result, item_key, self.item_code)
        else:
            st.success("✅ 패스워드 정책이 권장 기준을 충족합니다.")
        
        # 재진단 버튼
        ui_handler.show_rediagnose_button(item_key)
    
    def render_fix_form(self, result, item_key, ui_handler):
        """1.10 조치 폼 UI 렌더링"""
        st.markdown("**🔧 패스워드 정책 조치**")
        st.info("💡 권장 기준에 따라 IAM 계정 패스워드 정책을 업데이트합니다.")
        
        # 권장 설정 표시
        with st.expander("📋 적용될 권장 설정"):
            st.write("• **최소 길이:** 8자 이상")
            st.write("• **복잡도:** 대문자, 소문자, 숫자, 특수문자 모두 필요")
            st.write("• **최대 사용기간:** 90일")
            st.write("• **재사용 방지:** 5개 이전 패스워드")
            st.write("• **사용자 변경 허용:** 활성화")
            st.write("• **하드 만료:** 비활성화 (유연한 관리)")
        
        # 경고 메시지
        st.warning("⚠️ **주의사항**")
        st.write("• 패스워드 정책 변경은 기존 사용자에게 즉시 적용됩니다.")
        st.write("• 다음 패스워드 변경 시부터 새로운 정책이 적용됩니다.")
        st.write("• 현재 패스워드가 새 정책에 맞지 않아도 즉시 만료되지는 않습니다.")
        
        col_submit1, col_submit2 = st.columns(2)
        with col_submit1:
            if st.button("🔧 정책 업데이트 실행", key=f"execute_fix_{item_key}", type="primary"):
                fix_results = self.execute_fix({'update_policy': True})
                ui_handler._show_fix_results(fix_results)
                st.session_state[f'show_fix_{item_key}'] = False
                st.session_state[f'fix_completed_{item_key}'] = True
                st.rerun()
        
        with col_submit2:
            if st.button("❌ 취소", key=f"cancel_fix_{item_key}"):
                st.session_state[f'show_fix_{item_key}'] = False
                st.rerun()
            
    def execute_fix(self, selected_items):
        """조치 실행 (BaseChecker 추상 메서드 구현)"""
        if not selected_items.get('update_policy'):
            return [{"user": "계정 전체", "action": "패스워드 정책 업데이트", "status": "error", "error": "선택된 항목이 없습니다."}]
        
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = boto3.client('iam')
            
            # 권장 기준으로 패스워드 정책 업데이트
            iam.update_account_password_policy(
                MinimumPasswordLength=8,
                RequireSymbols=True,
                RequireNumbers=True,
                RequireUppercaseCharacters=True,
                RequireLowercaseCharacters=True,
                AllowUsersToChangePassword=True,
                MaxPasswordAge=90,
                PasswordReusePrevention=5,
                HardExpiry=False
            )
            
            return [{
                "user": "계정 전체",
                "action": "패스워드 정책 업데이트",
                "status": "success",
                "message": "권장 기준에 따라 패스워드 정책이 성공적으로 업데이트되었습니다."
            }]
            
        except ClientError as e:
            return [{
                "user": "계정 전체",
                "action": "패스워드 정책 업데이트",
                "status": "error",
                "error": f"정책 업데이트 실패: {str(e)}"
            }]
        except Exception as e:
            return [{
                "user": "계정 전체",
                "action": "패스워드 정책 업데이트",
                "status": "error",
                "error": f"예상치 못한 오류: {str(e)}"
            }]