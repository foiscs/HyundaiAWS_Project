"""
1.3 IAM 사용자 계정 식별 관리 진단
"""
import boto3
from ..base_checker import BaseChecker
import streamlit as st
from botocore.exceptions import ClientError

class IAMIdentificationChecker(BaseChecker):
    """1.3 IAM 사용자 계정 식별 관리 진단"""
    
    @property
    def item_code(self):
        return "1.3"
    
    @property 
    def item_name(self):
        return "IAM 사용자 계정 식별 관리"
    
    def run_diagnosis(self):
        """
        진단 수행
        - 모든 IAM 사용자가 식별을 위한 태그를 가지고 있는지 점검하고, 태그 없는 사용자 목록을 반환
        """
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = boto3.client('iam')
                
            untagged_users = []
            total_users = 0

            paginator = iam.get_paginator('list_users')
            for page in paginator.paginate():
                for user in page['Users']:
                    total_users += 1
                    user_name = user['UserName']
                    
                    # 사용자 태그 확인
                    tags_response = iam.list_user_tags(UserName=user_name)
                    tags = tags_response.get('Tags', [])
                    
                    if not tags:
                        untagged_users.append(user_name)

            # 위험도 계산
            untagged_count = len(untagged_users)
            risk_level = self.calculate_risk_level(
                untagged_count,
                1 if untagged_count > 0 else 0  # 태그 없는 사용자가 있으면 중간 위험도
            )

            return {
                "status": "success",
                "untagged_users": untagged_users,
                "untagged_count": untagged_count,
                "total_users": total_users,
                "risk_level": risk_level,
                "has_issues": untagged_count > 0
            }

        except ClientError as e:
            return {
                "status": "error",
                "error_message": str(e)
            }
    
    def render_result_ui(self, result, item_key, ui_handler):
        """1.3 진단 결과 UI 렌더링"""
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"🔍 **전체 사용자:** {result['total_users']}개")
        with col2:
            st.write(f"⚠️ **태그 없는 사용자:** {result['untagged_count']}개")
        
        if result['untagged_users']:
            with st.expander("태그가 없는 사용자 목록 보기"):
                for user in result['untagged_users']:
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
        """1.3 조치 폼 UI 렌더링"""
        with st.form(f"fix_form_{item_key}"):
            st.markdown("**🔧 조치할 사용자를 선택하세요:**")
            st.info("💡 선택된 사용자에게 식별용 태그(이름, 이메일, 부서 등)를 추가합니다.")
            
            # 사용자 선택
            selected_users = []
            for user in result['untagged_users']:
                if st.checkbox(f"`{user}`", key=f"user_{user}_{item_key}"):
                    selected_users.append(user)
            
            # 공통 태그 설정
            st.markdown("**태그 정보 입력:**")
            
            col1, col2 = st.columns(2)
            with col1:
                tag_name = st.text_input("이름", placeholder="예: 홍길동", key=f"tag_name_{item_key}")
                tag_department = st.text_input("부서", placeholder="예: IT보안팀", key=f"tag_dept_{item_key}")
            with col2:
                tag_email = st.text_input("이메일", placeholder="예: hong@company.com", key=f"tag_email_{item_key}")
                tag_role = st.text_input("역할", placeholder="예: 보안관리자", key=f"tag_role_{item_key}")
            
            col_submit1, col_submit2 = st.columns(2)
            with col_submit1:
                if st.form_submit_button("🔧 태그 추가 실행", type="primary"):
                    if selected_users:
                        fix_results = self.execute_fix({
                            'selected_users': selected_users,
                            'common_tags': {
                                'Name': tag_name,
                                'Email': tag_email, 
                                'Department': tag_department,
                                'Role': tag_role
                            }
                        })
                        ui_handler._show_fix_results(fix_results)
                        st.success("✅ 태그 추가 작업이 완료되었습니다!")
                        
                        # 조치 완료 후 상태 업데이트 (재진단은 form 밖에서)
                        st.session_state[f'show_fix_{item_key}'] = False
                        st.session_state[f'fix_completed_{item_key}'] = True
                        st.rerun()
                    else:
                        st.warning("⚠️ 조치할 사용자를 선택해주세요.")
            
            with col_submit2:
                if st.form_submit_button("❌ 취소"):
                    st.session_state[f'show_fix_{item_key}'] = False
                    st.rerun()
    
    def execute_fix(self, selected_items):
        """
        1.3 조치 실행
        - 선택된 사용자에게 태그 추가
        """
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = boto3.client('iam')
                
            results = []
            
            for user_name in selected_items.get('selected_users', []):
                try:
                    # 공통 태그 생성 (빈 값 제외)
                    tags = []
                    common_tags = selected_items.get('common_tags', {})
                    
                    for key, value in common_tags.items():
                        if value and value.strip():  # 빈 값이 아닌 경우에만 추가
                            tags.append({'Key': key, 'Value': value.strip()})
                    
                    # 기본 태그 추가 (생성일)
                    from datetime import datetime
                    tags.append({
                        'Key': 'CreatedBy', 
                        'Value': 'WALB-SecurityAutomation'
                    })
                    tags.append({
                        'Key': 'TaggedDate', 
                        'Value': datetime.now().strftime('%Y-%m-%d')
                    })
                    
                    if tags:
                        iam.tag_user(UserName=user_name, Tags=tags)
                        results.append({
                            "user": user_name, 
                            "action": "태그 추가", 
                            "status": "success",
                            "details": f"{len(tags)}개 태그 추가됨"
                        })
                    else:
                        results.append({
                            "user": user_name, 
                            "action": "태그 추가", 
                            "status": "skipped",
                            "details": "추가할 태그 정보가 없음"
                        })
                        
                except ClientError as e:
                    results.append({
                        "user": user_name, 
                        "action": "태그 추가", 
                        "status": "error", 
                        "error": str(e)
                    })
            
            return results
            
        except Exception as e:
            return [{"user": "전체", "action": "조치 실행", "status": "error", "error": str(e)}]