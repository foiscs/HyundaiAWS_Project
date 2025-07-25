"""
1.4 IAM 그룹 사용자 계정 관리 진단
"""
import boto3
from ..base_checker import BaseChecker
import streamlit as st
from botocore.exceptions import ClientError

class IAMGroupChecker(BaseChecker):
    """1.4 IAM 그룹 사용자 계정 관리 진단"""
    
    @property
    def item_code(self):
        return "1.4"
    
    @property 
    def item_name(self):
        return "IAM 그룹 사용자 계정 관리"
    
    def run_diagnosis(self):
        """
        진단 수행
        - 모든 IAM 사용자가 하나 이상의 그룹에 속해 있는지 점검하고, 미소속 사용자 목록을 반환
        """
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = boto3.client('iam')
                
            users_not_in_group = []
            total_users = 0

            paginator = iam.get_paginator('list_users')
            for page in paginator.paginate():
                for user in page['Users']:
                    total_users += 1
                    user_name = user['UserName']
                    
                    # 사용자가 속한 그룹 확인
                    groups_response = iam.list_groups_for_user(UserName=user_name)
                    if not groups_response.get('Groups'):
                        users_not_in_group.append(user_name)

            # 위험도 계산
            unassigned_count = len(users_not_in_group)
            risk_level = self.calculate_risk_level(
                unassigned_count,
                2 if unassigned_count > 3 else 1  # 많은 미소속 사용자는 더 심각
            )

            return {
                "status": "success",
                "users_not_in_group": users_not_in_group,
                "unassigned_count": unassigned_count,
                "total_users": total_users,
                "risk_level": risk_level,
                "has_issues": unassigned_count > 0
            }

        except ClientError as e:
            return {
                "status": "error",
                "error_message": str(e)
            }
    
    def render_result_ui(self, result, item_key, ui_handler):
        """1.4 진단 결과 UI 렌더링"""
        col1, col2 = st.columns(2)
        with col1:
            st.metric("전체 사용자", result.get('total_users', 0))
        with col2:
            st.metric("그룹 미소속", result.get('unassigned_count', 0))
        
        if result.get('users_not_in_group'):
            with st.expander("그룹에 속하지 않은 사용자 목록 보기"):
                for user in result['users_not_in_group']:
                    st.write(f"• `{user}`")
        
        # 조치 버튼
        if result.get('has_issues', False):
            if st.button("🔧 즉시 조치", key=f"fix_{item_key}"):
                st.session_state[f'show_fix_{item_key}'] = True
                st.rerun()
            
            if st.session_state.get(f'show_fix_{item_key}', False):
                ui_handler.show_fix_form(result, item_key, self.item_code)
        
        # 재진단 버튼
        ui_handler.show_rediagnose_button(item_key)
    
    def render_fix_form(self, result, item_key, ui_handler):
        """1.4 조치 폼 UI 렌더링"""
        st.markdown("**🔧 그룹에 속하지 않은 사용자 조치**")
        
        # 기존 그룹 목록 조회
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = boto3.client('iam')
            
            groups_response = iam.list_groups()
            available_groups = [group['GroupName'] for group in groups_response['Groups']]
            
            if not available_groups:
                st.warning("현재 IAM 그룹이 없습니다. 먼저 그룹을 생성해야 합니다.")
                
                # 새 그룹 생성 옵션
                with st.expander("새 그룹 생성"):
                    new_group_name = st.text_input("그룹 이름", placeholder="예: developers")
                    if st.button("그룹 생성", key=f"create_group_{item_key}"):
                        if new_group_name:
                            try:
                                iam.create_group(GroupName=new_group_name)
                                st.success(f"그룹 '{new_group_name}' 생성 완료!")
                                available_groups.append(new_group_name)
                                st.rerun()
                            except ClientError as e:
                                st.error(f"그룹 생성 실패: {str(e)}")
                        else:
                            st.error("그룹 이름을 입력하세요.")
            
            if available_groups:
                st.info(f"사용 가능한 그룹: {', '.join(available_groups)}")
                
                # 사용자별 그룹 할당
                user_group_assignments = {}
                
                for user in result['users_not_in_group']:
                    st.write(f"**사용자: `{user}`**")
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        selected_group = st.selectbox(
                            f"그룹 선택",
                            ["선택 안함"] + available_groups,
                            key=f"group_select_{user}_{item_key}"
                        )
                    
                    with col2:
                        assign_user = st.checkbox(
                            "할당",
                            key=f"assign_{user}_{item_key}"
                        )
                    
                    if assign_user and selected_group != "선택 안함":
                        user_group_assignments[user] = selected_group
                
                # 일괄 조치 실행
                col_submit1, col_submit2 = st.columns(2)
                with col_submit1:
                    if st.button("🚀 그룹 할당 실행", type="primary", key=f"execute_fix_{item_key}"):
                        if user_group_assignments:
                            results = ui_handler.engine._execute_group_assignment(user_group_assignments)
                            ui_handler._show_fix_results(results)
                            
                            # 조치 완료 후 폼 숨기기
                            st.session_state[f'show_fix_{item_key}'] = False
                            st.session_state[f'fix_completed_{item_key}'] = True
                            st.rerun()
                        else:
                            st.warning("할당할 사용자를 선택해주세요.")
                
                with col_submit2:
                    if st.button("❌ 취소", key=f"cancel_fix_{item_key}"):
                        st.session_state[f'show_fix_{item_key}'] = False
                        st.rerun()
        
        except ClientError as e:
            st.error(f"그룹 정보 조회 실패: {str(e)}")
    
    def show_rediagnose_button(self, item_key):
        """재진단 버튼 표시"""
        if st.button("🔄 재진단", key=f"rediagnose_{item_key}"):
            # 캐시된 진단 결과 제거
            if f'diagnosis_result_{item_key}' in st.session_state:
                del st.session_state[f'diagnosis_result_{item_key}']
            # 조치 폼 숨기기
            if f'show_fix_{item_key}' in st.session_state:
                del st.session_state[f'show_fix_{item_key}']
            st.rerun()
            
    def execute_fix(self, selected_items):
        """조치 실행 (BaseChecker 추상 메서드 구현)"""
        if 'user_group_assignments' in selected_items:
            return self._execute_group_assignment(selected_items['user_group_assignments'])
        else:
            return [{"user": "전체", "action": "조치 실행", "status": "error", "error": "선택된 항목이 없습니다."}]
        
    def _execute_group_assignment(self, user_group_assignments):
        """사용자 그룹 할당 실행"""
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = boto3.client('iam')
            
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