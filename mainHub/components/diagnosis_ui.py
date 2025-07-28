"""
WALB 진단 UI 통합 모듈
모든 UI 관련 기능을 통합한 단일 클래스 (페이지 + 컴포넌트 + 핸들러)

Classes:
- DiagnosisUI: 모든 진단 UI 기능을 담당하는 통합 클래스

Page Methods (페이지 렌더링):
- check_account_selection(): 선택된 계정 정보 확인
- render_sidebar(): 사이드바 렌더링 (진단 관리, 디버깅 정보)
- render_layout_controls(): 레이아웃 제어 버튼들 (일괄 진단, 레이아웃 선택)
- render_diagnosis_items(): 진단 항목들 렌더링 (1열/2열 레이아웃)
- handle_diagnosis_completion(): 전체 진단 완료 처리 및 자동 스크롤
- render_statistics_info(): 진단 항목 통계 정보 렌더링
- render_report_button(): 보고서 생성 버튼 렌더링

Component Methods (컴포넌트 렌더링):
- render_category_items(): 카테고리별 항목들 렌더링
- render_diagnosis_item(): 개별 진단 항목 카드 렌더링
- render_account_info_cards(): 계정 정보 카드들 렌더링
- show_diagnosis_result(): 진단 결과 표시 (체커별 위임)
- show_fix_form(): 조치 폼 표시 (체커별 위임)

Handler Methods (핸들러 기능):
- run_diagnosis(): 진단 실행 (엔진 위임)
- execute_fix(): 조치 실행 (엔진 위임)
- show_rediagnose_button(): 재진단 버튼 표시
- validate_environment(): 진단 환경 검증
"""

import streamlit as st
import streamlit.components.v1 as components
from .diagnosis_config import get_sk_shieldus_items, IMPORTANCE_COLORS, RISK_COLORS, DiagnosisDataConfig
from .diagnosis_templates import get_diagnosis_loading_template, get_account_card_template, get_risk_badge_template, get_scroll_script, get_diagnosis_completion_scroll
from .diagnosis_engine import DiagnosisCoreEngine
from .session_manager import SessionManager
from botocore.exceptions import ClientError

class DiagnosisUI:
    """진단 UI 통합 클래스 - 페이지/컴포넌트/핸들러 기능을 하나로 통합"""
    
    def __init__(self):
        self.engine = DiagnosisCoreEngine()
    
    # ================================
    # 페이지 렌더링 (기존 DiagnosisPageRenderer)
    # ================================
    
    def check_account_selection(self):
        """선택된 계정 정보 확인"""
        if 'selected_account' not in st.session_state:
            st.error("❌ 선택된 계정이 없습니다. 메인 페이지에서 계정을 선택해주세요.")
            if st.button("🏠 메인으로 돌아가기"):
                st.switch_page("main.py")
            return False
        return True
    
    def render_sidebar(self):
        """사이드바 렌더링"""
        with st.sidebar:
            # 전체 진단 진행 상태
            if st.session_state.get('full_diagnosis_running', False):
                st.markdown("### 🚀 전체 진단 진행 중")
                diagnosis_stats = SessionManager.get_diagnosis_stats()
                total_items = sum(diagnosis_stats.values())
                completed_items = diagnosis_stats['completed'] + diagnosis_stats['failed']
                
                if total_items > 0:
                    progress = completed_items / total_items
                    st.progress(progress)
                    st.write(f"**진행률:** {completed_items}/{total_items} ({progress*100:.1f}%)")
                st.divider()
            
            # 진단 관리
            if not st.session_state.get('full_diagnosis_running', False):
                st.markdown("### 🎛️ 진단 관리")
                
                # 레이아웃 선택 - 3:1:1 컬럼으로 구성
                layout_disabled = st.session_state.get('full_diagnosis_running', False)
                if 'layout_mode' not in st.session_state:
                    st.session_state.layout_mode = '2열'
                
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown("**🔄 진단항목 정렬**")
                
                with col2:
                    if st.button("1열", type="primary" if st.session_state.layout_mode == '1열' else "secondary", 
                                use_container_width=True, disabled=layout_disabled):
                        st.session_state.layout_mode = '1열'
                        st.rerun()
                    
                with col3:
                    if st.button("2열", type="primary" if st.session_state.layout_mode == '2열' else "secondary", 
                                use_container_width=True, disabled=layout_disabled):
                        st.session_state.layout_mode = '2열'
                        st.rerun()
                
                # 항목 펼치기/접기
                if st.session_state.get('expand_all_items', False):
                    if st.button("📁 모든 항목 접기", type="secondary", use_container_width=True):
                        st.session_state['expand_all_items'] = False
                        st.rerun()
                else:
                    if st.button("📂 모든 항목 펼치기", type="secondary", use_container_width=True):
                        st.session_state['expand_all_items'] = True
                        st.rerun()
                
                # 진단 결과 초기화
                if st.button("🗑️ 모든 진단 결과 초기화", type="secondary", use_container_width=True):
                    SessionManager.clear_diagnosis_states()
                    st.session_state['full_diagnosis_running'] = False
                    st.session_state['expand_all_items'] = False
                    st.success("모든 진단 결과가 초기화되었습니다.")
                    st.rerun()
                st.divider()
            
            # 디버깅 정보
            account = st.session_state.get('selected_account', {})
            st.markdown("### 🔧 진단 디버깅")
            st.markdown("#### 📡 연결 상태")
            connection_type = "🛡️ Role" if account.get('role_arn') else "🔑 Key"
            st.write(f"**연결 방식:** {connection_type}")
            st.write(f"**계정 ID:** `{account.get('account_id', 'N/A')}`")
            st.write(f"**리전:** `{account.get('primary_region', 'N/A')}`")
            
            # 세션 테스트
            st.markdown("#### 🧪 세션 테스트")
            if st.button("🔍 세션 연결 테스트", use_container_width=True):
                self.engine.test_session_connection(account)
    
    def render_layout_controls(self):
        """레이아웃 제어 버튼들"""
        # 전체 진단 버튼만 표시
        if st.button("🚀 전체 항목 일괄 진단", type="primary", use_container_width=True):
            total_items = SessionManager.run_full_diagnosis_setup()
            st.success(f"🚀 {total_items}개 항목의 전체 진단을 시작합니다!")
            st.rerun()

    def render_diagnosis_items(self):
        """진단 항목들 렌더링"""
        sk_items = get_sk_shieldus_items()
        categories = list(sk_items.items())
        layout_mode = st.session_state.get('layout_mode', '2열')
        
        if layout_mode == '1열':
            # 1열 레이아웃
            for category, items in categories:
                self.render_category_items(category, items, category.replace(' ', '_'))
                st.markdown("---")
        else:
            # 2열 레이아웃
            self._render_two_column_layout(categories)

    def _render_two_column_layout(self, categories):
        """2열 레이아웃 렌더링 헬퍼"""
        col1, col2 = st.columns(2)
        
        with col1:
            self.render_category_items(categories[0][0], categories[0][1], categories[0][0].replace(' ', '_'))
        
        with col2:
            self.render_category_items(categories[1][0], categories[1][1], categories[1][0].replace(' ', '_'))
            self.render_category_items(categories[2][0], categories[2][1], categories[2][0].replace(' ', '_'))
        
        st.markdown("---")
        
        # 운영 관리를 2열로 분할
        if len(categories) > 3:
            self._render_operation_management_split(categories[3])

    def _render_operation_management_split(self, operation_category):
        """운영 관리 카테고리를 2열로 분할 렌더링"""
        category_name, operation_items = operation_category
        half = len(operation_items) // 2
        
        col1, col2 = st.columns(2)
        
        # 첫 번째 절반
        with col1:
            st.subheader(f"📋 {category_name} (1-{half}) ({half}개 항목)")
            self._render_operation_items(operation_items[:half], category_name, 0)
        
        # 두 번째 절반
        with col2:
            remaining = len(operation_items) - half
            st.subheader(f"📋 {category_name} ({half+1}-{len(operation_items)}) ({remaining}개 항목)")
            self._render_operation_items(operation_items[half:], category_name, half)

    def _render_operation_items(self, items, category_name, start_index):
        """운영 관리 항목들 렌더링 헬퍼"""
        for index, item in enumerate(items, start=start_index):
            expanded = st.session_state.get('expand_all_items', False)
            code_text = item['code']
            name_text = item['name']
            
            # 한글 문자 길이 계산하여 고정폭 정렬
            name_display_length = sum(2 if ord(c) > 127 else 1 for c in name_text)
            spaces_needed = max(0, 35 - name_display_length)
            name_padded = name_text + " " * spaces_needed
            importance_part = f"{IMPORTANCE_COLORS.get(item['importance'], '⚪')} {item['importance']}"
            
            with st.expander(f"**{code_text}** | {name_padded} | {importance_part}", expanded=expanded):
                self.render_diagnosis_item(item, category_name.replace(' ', '_'), index)

    def handle_diagnosis_completion(self):
        """전체 진단 완료 처리"""
        if st.session_state.get('full_diagnosis_running', False):
            diagnosis_stats = SessionManager.get_diagnosis_stats()
            total_items = sum(diagnosis_stats.values())
            completed_items = diagnosis_stats['completed'] + diagnosis_stats['failed']
            
            if total_items > 0 and completed_items == total_items:
                st.session_state['full_diagnosis_running'] = False
                st.session_state['diagnosis_completed'] = True
                st.success("🎉 전체 진단이 완료되었습니다!")
                st.rerun()
        
        # 진단 완료 후 자동 스크롤
        if st.session_state.get('diagnosis_completed', False):
            self._auto_scroll_to_results()
            st.session_state['diagnosis_completed'] = False

    def _auto_scroll_to_results(self):
        """진단 완료 후 자동 스크롤 - templates의 기존 함수 활용"""
        components.html(get_diagnosis_completion_scroll(), height=0)

    def render_statistics_info(self):
        """진단 항목 통계 정보 렌더링"""
        config = DiagnosisDataConfig()
        total_items = config.get_total_items_count()
        risk_counts = config.get_items_by_risk_level()
        
        st.info(f"📊 **총 {total_items}개** 보안 진단 항목 | 🔴 상위험 {risk_counts['상']}개 | 🟡 중위험 {risk_counts['중']}개 | 🟢 저위험 {risk_counts['하']}개")

    def render_report_button(self):
        """보고서 생성 버튼 렌더링"""
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("📊 진단 보고서 생성", type="primary", use_container_width=True):
                st.info("보고서 생성 기능 (준비중)")
    
    # ================================
    # 컴포넌트 렌더링 (기존 DiagnosisUIComponents)
    # ================================
    
    def render_category_items(self, category, items, category_key):
        """카테고리 항목들 렌더링"""
        st.subheader(f"📋 {category} ({len(items)}개 항목)")
        
        for index, item in enumerate(items):
            expanded = st.session_state.get('expand_all_items', False)
            
            # expander 제목 생성
            title = self._create_expander_title(item)
            
            with st.expander(title, expanded=expanded):
                self.render_diagnosis_item(item, category_key, index)

    def _create_expander_title(self, item):
        """expander 제목 생성 헬퍼"""
        code_text = item['code']  
        name_text = item['name']
        importance_part = f"{IMPORTANCE_COLORS.get(item['importance'], '⚪')} {item['importance']}"
        
        # 한글 문자 길이 계산하여 고정폭 정렬
        name_display_length = sum(2 if ord(c) > 127 else 1 for c in name_text)
        spaces_needed = max(0, 35 - name_display_length)
        name_padded = name_text + " " * spaces_needed
        
        return f"**{code_text}** | {name_padded} | {importance_part}"
    
    def render_diagnosis_item(self, item, category, index):
        """진단 항목 카드 렌더링"""
        importance_color = IMPORTANCE_COLORS.get(item["importance"], "⚪")
        item_key = f"{category}_{index}"
        container_id = f"diagnosis_item_{item_key}"
        
        with st.container():
            diagnosis_status = st.session_state.get(f'diagnosis_status_{item_key}', 'idle')
            diagnosis_result = st.session_state.get(f'diagnosis_result_{item_key}', None)
            
            # 상태별 스타일
            status_text, status_color = self._get_status_display(diagnosis_status, diagnosis_result)
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                self._render_item_info(item, status_text, status_color, importance_color)
                
            with col2:
                self._render_diagnosis_button(item_key, diagnosis_status)
                self._render_risk_badge(diagnosis_status, diagnosis_result)
            
            # 진단 실행 처리
            if diagnosis_status == 'running':
                self._handle_diagnosis_execution(item, item_key, container_id)
            
            # 진단 결과 표시
            if diagnosis_status == 'completed' and diagnosis_result:
                self._handle_diagnosis_results(diagnosis_result, item_key, item['code'])
    
    def _get_status_display(self, diagnosis_status, diagnosis_result):
        """진단 상태 표시 정보 반환"""
        if diagnosis_status == 'idle':
            return "⏳ 대기중", "#718096"
        elif diagnosis_status == 'running':
            return "🔄 진단중...", "#3182ce"
        elif diagnosis_status == 'completed':
            if diagnosis_result and diagnosis_result.get('status') == 'success':
                risk_level = diagnosis_result.get('risk_level', 'unknown')
                risk_icon = RISK_COLORS.get(risk_level, ("⚪", "#718096", "알수없음"))[0]
                return f"✅ 완료 {risk_icon}", "#38a169"
            else:
                return "❌ 실패", "#e53e3e"
    
    def _render_item_info(self, item, status_text, status_color, importance_color):
        """항목 정보 렌더링"""
        st.markdown(f"""
        <div class="diagnosis-card">
            <div class="diagnosis-header">{item['code']} {item['name']}</div>
            <div class="diagnosis-description">📝 {item['description']}</div>
            <div class="diagnosis-meta">
                <span><strong>중요도:</strong> {importance_color} {item['importance']}</span>
                <span><strong>상태:</strong> <span style="color: {status_color};">{status_text}</span></span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_diagnosis_button(self, item_key, diagnosis_status):
        """진단 버튼 렌더링"""
        if diagnosis_status != 'running':
            if st.button("🔍 진단", key=f"diagnose_{item_key}", use_container_width=True):
                st.session_state[f'diagnosis_status_{item_key}'] = 'running'
                st.rerun()
        else:
            st.markdown("""
            <div style="text-align: center; padding: 8px;">
                <div style="color: #3182ce; font-weight: 500;">🔄 진행중</div>
            </div>
            """, unsafe_allow_html=True)
    
    def _render_risk_badge(self, diagnosis_status, diagnosis_result):
        """위험도 배지 렌더링"""
        if diagnosis_status == 'completed' and diagnosis_result:
            risk_level = diagnosis_result.get('risk_level', 'unknown')
            if risk_level != 'unknown' and risk_level in RISK_COLORS:
                icon, color, text = RISK_COLORS[risk_level]
                st.markdown(get_risk_badge_template(icon, color, text), unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="
                    text-align: center; 
                    padding: 4px 8px;
                    margin-top: 8px;
                    color: #38a169; 
                    font-weight: 500;
                    font-size: 0.9rem;
                ">✅ 완료</div>
                """, unsafe_allow_html=True)
    
    def _handle_diagnosis_execution(self, item, item_key, container_id):
        """진단 실행 처리"""
        # 자동 스크롤
        if st.session_state.get('full_diagnosis_running', False):
            components.html(get_scroll_script(container_id), height=0)
        
        # 로딩 표시
        st.markdown(get_diagnosis_loading_template(item['name']), unsafe_allow_html=True)
        
        # 실제 진단 실행
        result = self.engine.run_diagnosis(item['code'], item['name'])
        st.session_state[f'diagnosis_result_{item_key}'] = result
        st.session_state[f'diagnosis_status_{item_key}'] = 'completed'
        st.rerun()
    
    def _handle_diagnosis_results(self, diagnosis_result, item_key, item_code):
        """진단 결과 처리"""
        st.markdown("---")
        
        if diagnosis_result.get('status') == 'success':
            self.show_diagnosis_result(diagnosis_result, item_key, item_code)
            
            # 조치 폼 표시
            if st.session_state.get(f'show_fix_{item_key}', False):
                st.markdown("---")
                self.show_fix_form(diagnosis_result, item_key, item_code)
                
        elif diagnosis_result.get('status') == 'not_implemented':
            st.info(diagnosis_result.get('message', '구현되지 않음'))
        else:
            st.error(f"❌ 진단 실패: {diagnosis_result.get('error_message', '알 수 없는 오류')}")

    def render_account_info_cards(self, account):
        """계정 정보 카드들 렌더링"""
        col1, col2, col3, col4, col5 = st.columns(5)
        
        cards_data = [
            (True, "계정 이름", account.get('cloud_name', 'Unknown')),
            (False, "계정 ID", account.get('account_id', 'N/A')),
            (False, "리전", account.get('primary_region', 'N/A')),
            (False, "연결 방식", f"{'🛡️ ' if account.get('role_arn') else '🔑 '}{'Role 인증' if account.get('role_arn') else 'Access Key'}"),
            (False, "담당자", account.get('contact_email', 'N/A'))
        ]
        
        columns = [col1, col2, col3, col4, col5]
        
        for i, (is_primary, label, value) in enumerate(cards_data):
            with columns[i]:
                st.markdown(get_account_card_template("info", label, value, is_primary), unsafe_allow_html=True)
    
    def show_diagnosis_result(self, result, item_key, item_code):
        """진단 결과 표시 - 체커별 위임"""
        checker = self.engine.get_diagnosis_checker(item_code)
        if checker and hasattr(checker, 'render_result_ui'):
            checker.render_result_ui(result, item_key, self)
        else:
            self._show_default_result(result)
    
    def _show_default_result(self, result):
        """기본 진단 결과 표시"""
        st.write("📊 진단 결과가 표시됩니다.")
        if result.get('has_issues', False):
            st.warning("⚠️ 보안 이슈가 발견되었습니다.")
    
    def show_fix_form(self, result, item_key, item_code):
        """조치 폼 표시 - 체커별 위임"""
        checker = self.engine.get_diagnosis_checker(item_code)
        if checker and hasattr(checker, 'render_fix_form'):
            checker.render_fix_form(result, item_key, self)
        else:
            st.info("조치 기능이 구현되지 않았습니다.")
    
    # ================================
    # 핸들러 기능 (기존 DiagnosisUIHandler)
    # ================================
    
    def run_diagnosis(self, item_code, item_name):
        """진단 실행 - 엔진 위임"""
        return self.engine.run_diagnosis(item_code, item_name)
    
    def execute_fix(self, selected_items, item_key, item_code):
        """조치 실행 - 엔진 위임"""
        results = self.engine.execute_fix(selected_items, item_key, item_code)
        
        # 조치 실행 후 상태 업데이트
        with st.spinner("조치를 실행하고 있습니다..."):
            self._show_fix_results(results)
            st.session_state[f'show_fix_{item_key}'] = False
            st.session_state[f'fix_completed_{item_key}'] = True
            st.rerun()
    
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
        """재진단 버튼 표시"""
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
    
    
    def validate_environment(self):
        """진단 환경 검증"""
        return self.engine.validate_diagnosis_environment()