"""
1.8 Access Key 활성화 및 사용주기 관리 진단 및 조치
SK Shieldus 41개 항목 AWS 보안 진단
"""

import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timezone
import streamlit as st
from ..base_checker import BaseChecker

class AccessKeyManagement18(BaseChecker):
    """1.8 Access Key 활성화 및 사용주기 관리"""
    
    def __init__(self):
        super().__init__()
        self.description = "루트 계정 Access Key 존재 여부 및 IAM 사용자 키 생명주기 관리"
    
    @property
    def item_code(self):
        return "1.8"
    
    @property
    def item_name(self):
        return "Access Key 활성화 및 사용주기 관리"
    
    def run_diagnosis(self):
        """1.8 진단 실행"""
        try:
            iam = self.session.client('iam')
            findings = {
                'root_key_exists': False,
                'old_keys': [],
                'unused_keys': []
            }
            now = datetime.now(timezone.utc)

            # 루트 계정 Access Key 존재 여부 확인
            summary = iam.get_account_summary()
            if summary['SummaryMap'].get('AccountAccessKeysPresent', 0) > 0:
                findings['root_key_exists'] = True

            # IAM 사용자 키 점검
            for user in iam.list_users()['Users']:
                user_name = user['UserName']
                for key in iam.list_access_keys(UserName=user_name)['AccessKeyMetadata']:
                    if key['Status'] == 'Active':
                        access_key_id = key['AccessKeyId']
                        create_date = key['CreateDate']
                        
                        # 생성 후 60일 초과
                        if (now - create_date).days > 60:
                            findings['old_keys'].append({
                                'user': user_name,
                                'key_id': access_key_id,
                                'days': (now - create_date).days
                            })

                        # 마지막 사용 정보 조회
                        try:
                            last_used_info = iam.get_access_key_last_used(AccessKeyId=access_key_id)
                            last_used_date = last_used_info.get('AccessKeyLastUsed', {}).get('LastUsedDate')
                            
                            # 30일 초과 미사용 or 사용 이력 없음
                            if last_used_date and (now - last_used_date).days > 30:
                                findings['unused_keys'].append({
                                    'user': user_name,
                                    'key_id': access_key_id,
                                    'days': (now - last_used_date).days
                                })
                            elif not last_used_date and (now - create_date).days > 30:
                                findings['unused_keys'].append({
                                    'user': user_name,
                                    'key_id': access_key_id,
                                    'days': (now - create_date).days,
                                    'note': '사용기록 없음'
                                })
                        except ClientError:
                            # 일부 키는 last used 정보 조회가 실패할 수 있음
                            pass

            # 위험도 계산
            issue_count = len(findings['old_keys']) + len(findings['unused_keys'])
            if findings['root_key_exists']:
                issue_count += 10  # 루트 키 존재는 매우 심각

            risk_level = self.calculate_risk_level(
                issue_count,
                3 if findings['root_key_exists'] else 2
            )

            return {
                "status": "success",
                "root_key_exists": findings['root_key_exists'],
                "old_keys": findings['old_keys'],
                "unused_keys": findings['unused_keys'],
                "old_keys_count": len(findings['old_keys']),
                "unused_keys_count": len(findings['unused_keys']),
                "risk_level": risk_level,
                "has_issues": findings['root_key_exists'] or findings['old_keys'] or findings['unused_keys']
            }

        except ClientError as e:
            return {
                "status": "error",
                "error_message": str(e)
            }
    
    def render_result_ui(self, result, item_key, ui_handler):
        """1.8 진단 결과 UI 렌더링"""
        # 루트 계정 Access Key 상태
        if result.get('root_key_exists'):
            st.error("🚨 **루트 계정에 Access Key가 존재합니다!**")
            st.warning("⚠️ 루트 계정 Access Key는 즉시 삭제해야 합니다.")
        else:
            st.success("✅ **루트 계정에 Access Key가 존재하지 않습니다.**")
        
        # 오래된 키 정보
        if result.get('old_keys_count', 0) > 0:
            st.warning(f"⚠️ **생성 후 60일이 경과한 Access Key:** {result['old_keys_count']}개")
            with st.expander("60일 초과 키 목록 보기"):
                for key in result.get('old_keys', []):
                    st.write(f"• `{key['user']}` - {key['key_id']} (생성 {key['days']}일 경과)")
        
        # 미사용 키 정보
        if result.get('unused_keys_count', 0) > 0:
            st.warning(f"⚠️ **30일 이상 사용되지 않은 Access Key:** {result['unused_keys_count']}개")
            with st.expander("미사용 키 목록 보기"):
                for key in result.get('unused_keys', []):
                    note = f" ({key.get('note')})" if 'note' in key else ""
                    st.write(f"• `{key['user']}` - {key['key_id']} (미사용 {key['days']}일{note})")
        
        if not result.get('has_issues'):
            st.success("✅ **모든 Access Key가 보안 기준을 충족합니다.**")
        
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
        """1.8 조치 폼 UI 렌더링"""
        st.markdown("**🔧 Access Key 조치 옵션:**")
        
        # 루트 키 조치 안내
        if result.get('root_key_exists'):
            st.error("**🚨 루트 계정 Access Key 조치**")
            st.markdown("""
            루트 계정에 Access Key가 존재합니다. 이는 매우 위험하므로 즉시 삭제해야 합니다.
            
            **수동 삭제 방법:**
            1. AWS 콘솔 로그인
            2. 우측 상단 계정명 클릭 → '내 보안 자격 증명'
            3. 'Access Keys' 섹션에서 키 삭제
            """)
            st.warning("⚠️ 루트 키는 보안상의 이유로 자동 삭제가 제한됩니다.")
        
        # 미사용 키 조치
        unused_keys = result.get('unused_keys', [])
        if unused_keys:
            with st.container():
                st.markdown("**⚠️ 미사용 Access Key 조치 (30일 이상 미사용)**")
                st.warning("⚠️ 선택된 키가 비활성화 또는 삭제됩니다. 신중히 선택하세요.")
                
                selected_keys = []
                for key in unused_keys:
                    note = f" ({key.get('note')})" if 'note' in key else ""
                    if st.checkbox(
                        f"{key['user']} - {key['key_id']} (미사용 {key['days']}일{note})", 
                        key=f"unused_{key['key_id']}"
                    ):
                        selected_keys.append(key)
                
                if selected_keys:
                    action_type = st.radio(
                        "조치 방법을 선택하세요:",
                        ["비활성화 (Inactive)", "완전 삭제"],
                        key=f"action_type_{item_key}"
                    )
                    
                    if st.button("🚀 선택된 키 조치 실행", key=f"execute_unused_{item_key}"):
                        ui_handler.execute_fix(
                            {"keys": selected_keys, "action": action_type}, 
                            item_key, 
                            self.item_code
                        )
        
        # 오래된 키 안내
        old_keys = result.get('old_keys', [])
        if old_keys:
            st.info("**ℹ️ 생성된 지 60일 이상 경과한 키 (키 교체 권장)**")
            for key in old_keys:
                st.write(f"• `{key['user']}` - {key['key_id']} (생성 {key['days']}일 경과)")
            st.markdown("""
            **권장 조치:**
            1. 새로운 Access Key 생성
            2. 애플리케이션에서 새 키로 업데이트
            3. 기존 키 삭제
            
            ⚠️ 오래된 키는 수동으로 교체하는 것을 권장합니다.
            """)

    def execute_fix(self, selected_items):
        """1.8 조치 실행"""
        try:
            iam = self.session.client('iam')
            results = []
            
            keys = selected_items.get('keys', [])
            action = selected_items.get('action', '비활성화 (Inactive)')
            
            for key in keys:
                try:
                    if action == "비활성화 (Inactive)":
                        iam.update_access_key(
                            UserName=key['user'],
                            AccessKeyId=key['key_id'],
                            Status='Inactive'
                        )
                        results.append({
                            "status": "success",
                            "user": key['user'],
                            "action": f"Access Key 비활성화 완료 ({key['key_id']})"
                        })
                    elif action == "완전 삭제":
                        iam.delete_access_key(
                            UserName=key['user'],
                            AccessKeyId=key['key_id']
                        )
                        results.append({
                            "status": "success",
                            "user": key['user'],
                            "action": f"Access Key 삭제 완료 ({key['key_id']})"
                        })
                except ClientError as e:
                    results.append({
                        "status": "error",
                        "user": key['user'],
                        "error": str(e)
                    })
            
            return results
            
        except Exception as e:
            return [{
                "status": "error", 
                "user": "전체",
                "error": str(e)
            }]