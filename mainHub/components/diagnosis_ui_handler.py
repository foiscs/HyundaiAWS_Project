"""
진단 UI 핸들러 - 진단 결과 표시 및 조치 로직 중앙화
"""
import streamlit as st
from .sk_diagnosis import get_checker
from .aws_handler import AWSConnectionHandler
from botocore.exceptions import ClientError

class DiagnosisUIHandler:
    """진단 UI 처리 중앙화 클래스"""
    
    def __init__(self):
        self.aws_handler = self._get_aws_handler()
    
    def _get_aws_handler(self):
        """AWS 핸들러 싱글톤 패턴으로 가져오기"""
        if 'aws_handler' not in st.session_state:
            st.session_state.aws_handler = AWSConnectionHandler()
        return st.session_state.aws_handler
    
    def _create_session(self):
        """AWS 세션 생성 - 중복 로직 제거"""
        account = st.session_state.selected_account
        
        if account.get('role_arn'):
            return self.aws_handler.create_session_from_role(
                role_arn=account['role_arn'],
                external_id=account.get('external_id'),
                region=account['primary_region']
            )
        else:
            return self.aws_handler.create_session_from_keys(
                access_key_id=account['access_key_id'],
                secret_access_key=account['secret_access_key'],
                region=account['primary_region']
            )
    
    def run_diagnosis(self, item_code, item_name):
        """진단 실행 - 통합 로직"""
        checker = get_checker(item_code)
        if not checker:
            return {
                "status": "not_implemented",
                "message": f"{item_name} 진단 기능이 아직 구현되지 않았습니다."
            }
        
        try:
            session = self._create_session()
            checker.session = session
            
            with st.spinner(f"{item_name}을(를) 분석하고 있습니다..."):
                return checker.run_diagnosis()
                
        except Exception as e:
            return {
                "status": "error",
                "error_message": str(e)
            }
    
    def show_diagnosis_result(self, result, item_key, item_code):
        """진단 결과 표시 - 체커별 위임"""
        checker = get_checker(item_code)
        if checker and hasattr(checker, 'render_result_ui'):
            # 체커가 자체 UI 렌더링 메서드를 가지고 있으면 위임
            checker.render_result_ui(result, item_key, self)
        else:
            # 기본 결과 표시
            self._show_default_result(result, item_key, item_code)
    
    def _show_default_result(self, result, item_key, item_code):
        """기본 진단 결과 표시"""
        st.write("📊 진단 결과가 표시됩니다.")
        if result.get('has_issues', False):
            st.warning("⚠️ 보안 이슈가 발견되었습니다.")
    
    def show_fix_form(self, result, item_key, item_code):
        """조치 폼 표시 - 체커별 위임"""
        checker = get_checker(item_code)
        if checker and hasattr(checker, 'render_fix_form'):
            checker.render_fix_form(result, item_key, self)
        else:
            st.info("조치 기능이 구현되지 않았습니다.")
    
    def execute_fix(self, selected_items, item_key, item_code):
        """조치 실행 - 통합 로직"""
        checker = get_checker(item_code)
        if not checker:
            st.error("조치 기능을 찾을 수 없습니다.")
            return
        
        try:
            session = self._create_session()
            checker.session = session
            
            with st.spinner("조치를 실행하고 있습니다..."):
                results = checker.execute_fix(selected_items)
                
                # 결과 표시
                self._show_fix_results(results)
                
                # 조치 완료 후 상태 업데이트
                st.session_state[f'show_fix_{item_key}'] = False
                st.session_state[f'fix_completed_{item_key}'] = True
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ 조치 실행 중 오류: {str(e)}")
    def _execute_group_assignment(self, user_group_assignments):
        """사용자 그룹 할당 실행"""
        try:
            account = st.session_state.selected_account
            
            if account.get('role_arn'):
                session = self.aws_handler.create_session_from_role(
                    role_arn=account['role_arn'],
                    external_id=account.get('external_id'),
                    region=account['primary_region']
                )
            else:
                session = self.aws_handler.create_session_from_keys(
                    access_key_id=account['access_key_id'],
                    secret_access_key=account['secret_access_key'],
                    region=account['primary_region']
                )
            
            iam = session.client('iam')
            results = []
            
            for user_name, group_name in user_group_assignments.items():
                try:
                    iam.add_user_to_group(UserName=user_name, GroupName=group_name)
                    results.append({
                        "user": user_name,
                        "action": f"그룹 '{group_name}'에 추가",
                        "status": "success"
                    })
                except ClientError as e:
                    results.append({
                        "user": user_name,
                        "action": f"그룹 '{group_name}'에 추가",
                        "status": "error",
                        "error": str(e)
                    })
            
            return results
            
        except Exception as e:
            return [{
                "user": "전체",
                "action": "그룹 할당",
                "status": "error",
                "error": str(e)
            }]
    def _show_fix_results(self, results):
        """조치 결과 표시"""
        st.subheader("📊 조치 결과")
        for result in results:
            if result.get("status") == "success":
                action_text = result.get('action', ', '.join(result.get('actions', [])))
                st.success(f"✅ {result['user']}: {action_text} 완료")
            elif result.get("status") == "no_action":
                st.info(f"ℹ️ {result['user']}: {result.get('message', '조치할 항목 없음')}")
            elif result.get("status") == "already_done":
                st.info(f"ℹ️ {result['user']}: 이미 처리됨")
            else:
                error_msg = result.get('error', result.get('error_message', '알 수 없는 오류'))
                st.error(f"❌ {result['user']}: 실패 - {error_msg}")
    
    def show_rediagnose_button(self, item_key):
        """재진단 버튼 표시 - 공통 로직"""
        if st.session_state.get(f'fix_completed_{item_key}', False):
            st.success("✅ 조치가 완료되었습니다!")
            if st.button("🔄 재진단", key=f"rediagnose_{item_key}"):
                # 기존 결과 삭제하고 재진단
                keys_to_delete = [
                    f'diagnosis_result_{item_key}',
                    f'diagnosis_status_{item_key}',
                    f'fix_completed_{item_key}'
                ]
                for key in keys_to_delete:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()