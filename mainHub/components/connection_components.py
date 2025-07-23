"""
컴포넌트 목록:
- step_indicator: WALB 4단계 진행 표시기 (완료/진행중/대기 상태)
- connection_type_card: 보안 연결방식 선택 카드 (Role/AccessKey 비교)
- info_box: 보안 등급별 정보박스 (info/warning/error/success 타입)
- json_code_block: AWS IAM 정책 JSON 표시 + 구문강조 + 복사 기능
- test_result_table: AWS 서비스별 권한 테스트 결과 테이블 (7개 서비스)
- loading_spinner: AWS API 호출 중 로딩 스피너 + 진행 메시지
- connection_test_result: boto3 연결 테스트 종합 결과 화면
- input_field_with_toggle: 비밀번호 토글 입력 필드 (보안 강화)
- navigation_buttons: 4단계 네비게이션 버튼 (조건부 활성화)
- sidebar_panel: 멀티클라우드 모니터링 사이드바 (상태/디버그/세션관리)

🔧 유틸리티 함수:
- reset_session_state: 안전한 세션 초기화 (민감정보 정리)
- validate_and_show_error: AWS 입력값 실시간 검증 + 에러 표시
- safe_session_update: 중복 방지 세션 상태 업데이트
- get_actual_secret_key: 마스킹된 Secret Key 실제값 반환
- cleanup_sensitive_data: 보안을 위한 민감정보 자동 정리
"""

import streamlit as st
import streamlit.components.v1 as components
import json
import time
from components.aws_handler import AWSConnectionHandler

def step_indicator(current_step):
    """
    4단계 진행 표시기 컴포넌트 - Components로 완전 커스터마이징
    - 사진과 같은 스타일의 카드형 배경과 테두리 적용
    """
    steps = [
        {"number": 1, "title": "연결 방식 선택"},
        {"number": 2, "title": "권한 설정"},
        {"number": 3, "title": "연결 정보 입력"},
        {"number": 4, "title": "연결 테스트"}
    ]
    
    # 단계별 HTML 생성
    step_items_html = ""
    for i, step in enumerate(steps):
        # 단계 상태 결정
        if step["number"] < current_step:
            status = "completed"
            icon = "✅"
            circle_class = "step-completed"
            title_class = "title-completed"
        elif step["number"] == current_step:
            status = "active"
            icon = str(step["number"])
            circle_class = "step-active"
            title_class = "title-active"
        else:
            status = "pending"
            icon = str(step["number"])
            circle_class = "step-pending"
            title_class = "title-pending"
        
        # 단계 아이템 HTML
        step_items_html += f'''
        <div class="step-item">
            <div class="step-circle {circle_class}">{icon}</div>
            <span class="step-title {title_class}">{step["title"]}</span>
        </div>
        '''
        
        # 연결선 추가 (마지막 단계 제외)
        if i < len(steps) - 1:
            step_items_html += '<div class="step-connector"></div>'
    
    # HTML 코드
    step_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
        }}
        .step-container {{
            background: white;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            padding: 1.5rem 2rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 1rem 0;
        }}
        .step-item {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}
        .step-circle {{
            width: 2.5rem;
            height: 2.5rem;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 0.875rem;
        }}
        .step-completed {{
            background-color: #10B981;
            color: white;
        }}
        .step-active {{
            background-color: #3B82F6;
            color: white;
        }}
        .step-pending {{
            background-color: #E5E7EB;
            color: #6B7280;
        }}
        .step-title {{
            font-size: 0.875rem;
            font-weight: 500;
        }}
        .title-completed {{
            color: #10B981;
        }}
        .title-active {{
            color: #3B82F6;
        }}
        .title-pending {{
            color: #6B7280;
        }}
        .step-connector {{
            flex: 1;
            height: 2px;
            background-color: #E5E7EB;
            margin: 0 1rem;
            border-radius: 1px;
        }}
        </style>
    </head>
    <body>
        <div class="step-container">
            {step_items_html}
        </div>
    </body>
    </html>
    """
    
    # Components로 렌더링
    components.html(step_html, height=120)

def connection_type_card(title, description, pros, is_selected, icon, card_type="role"):
    """
    연결 방식 선택 카드 - 라디오 버튼 방식으로 변경
    """
    # 선택 상태에 따른 스타일
    if is_selected:
        border_color = "#3B82F6" if card_type == "role" else "#F59E0B"
        bg_color = "#EFF6FF" if card_type == "role" else "#FFFBEB"
    else:
        border_color = "#E5E7EB"
        bg_color = "white"
    
    # 장점 리스트 HTML
    pros_html = ""
    for pro in pros:
        color = "#10B981" if "✓" in pro else "#F59E0B" if "⚠" in pro else "#6B7280"
        pros_html += f'<span style="color: {color}; margin-right: 1rem; font-size: 0.75rem;">{pro}</span>'
    
    # 카드 HTML
    st.markdown(
        f"""
        <div style="
            background-color: {bg_color};
            border: 2px solid {border_color};
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
        ">
            <div style="display: flex; align-items: flex-start; gap: 0.75rem;">
                <div style="font-size: 1.5rem; margin-top: 0.25rem;">{icon}</div>
                <div style="flex: 1;">
                    <h3 style="margin: 0 0 0.25rem 0; font-weight: 600; color: #111827;">{title}</h3>
                    <p style="margin: 0 0 0.5rem 0; font-size: 0.875rem; color: #6B7280; line-height: 1.4;">{description}</p>
                    <div>{pros_html}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # 선택 버튼
    return st.button(f"📍 {title} 선택", key=f"select_{card_type}", use_container_width=True)

def info_box(message, box_type="info", title=None):
    """
    정보/경고/에러 박스 컴포넌트
    - 타입별로 다른 색상과 아이콘 사용
    - 제목과 메시지를 구분하여 표시
    
    Args:
        message (str): 표시할 메시지
        box_type (str): 박스 타입 ("info", "warning", "error", "success")
        title (str, optional): 박스 제목
    """
    # 타입별 아이콘 매핑
    icons = {
        "info": "📘",
        "warning": "⚠️",
        "error": "❌",
        "success": "✅"
    }
    
    icon = icons.get(box_type, "📘")
    
    # 제목 HTML (있는 경우만)
    title_html = f'<div class="info-box-title">{title}</div>' if title else ""
    
    # 박스 HTML
    box_html = f'''
    <div class="info-box {box_type}">
        <div style="font-size: 1.25rem;">{icon}</div>
        <div class="info-box-content">
            {title_html}
            <div class="info-box-text">{message}</div>
        </div>
    </div>
    '''
    
    st.markdown(box_html, unsafe_allow_html=True)

def json_code_block(json_data, title, show_copy_button=True):
    """
    JSON 정책 표시 - Streamlit Components로 완전 커스터마이징
    """
    # JSON을 예쁘게 포맷팅
    formatted_json = json.dumps(json_data, indent=2, ensure_ascii=False)
    
    # 제목 표시
    st.subheader(f"📄 {title}")
    
    # 구체적인 안내 메시지
    if "신뢰 관계" in title:
        st.info("💡 **AWS IAM 콘솔 → Roles → 생성할 Role → Trust relationships → Edit trust policy**에 아래 JSON을 붙여넣으세요.")
    elif "권한 정책" in title:
        st.info("💡 **AWS IAM 콘솔 → Policies → Create policy → JSON 탭**에 아래 JSON을 붙여넣으세요.")
    else:
        st.info("💡 아래 JSON 코드를 복사하여 AWS IAM 설정에 사용하세요.")
    
    # Components로 JSON 코드 블록 렌더링
    json_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: 'SFMono-Regular', 'Monaco', 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
        }}
        .json-container {{
            background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%);
            border: 1px solid #4a5568;
            border-left: 4px solid #4299e1;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
            overflow-x: auto;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            user-select: text;
            cursor: text;
        }}
        .json-code {{
            color: #e2e8f0;
            margin: 0;
            line-height: 1.5;
            font-size: 0.875rem;
            white-space: pre;
            overflow-x: auto;
        }}
        /* JSON 구문 강조 */
        .json-key {{ color: #ffd700; }}
        .json-string {{ color: #98fb98; }}
        .json-number {{ color: #87ceeb; }}
        .json-boolean {{ color: #dda0dd; }}
        .json-null {{ color: #ff6347; }}
        .json-bracket {{ color: #ba68c8; }}
        .json-comma {{ color: #90a4ae; }}
        </style>
    </head>
    <body>
        <div class="json-container">
            <pre class="json-code" id="jsonCode">{formatted_json}</pre>
        </div>
        
        <script>
        
        // JSON 구문 강조 적용
        function highlightJSON() {{
            const codeElement = document.getElementById('jsonCode');
            let code = codeElement.innerHTML;
            
            // 문자열 (녹색)
            code = code.replace(/"([^"\\\\]*(\\\\.[^"\\\\]*)*)"/g, '<span class="json-string">"$1"</span>');
            
            // 키 (황금색) - 콜론 앞의 문자열
            code = code.replace(/(<span class="json-string">"[^"]*"<\\/span>)(\s*:)/g, '<span class="json-key">$1</span>$2');
            
            // 숫자 (하늘색)
            code = code.replace(/:\s*(-?\d+\.?\d*)/g, ': <span class="json-number">$1</span>');
            
            // 불린값 (보라색)
            code = code.replace(/:\s*(true|false)/g, ': <span class="json-boolean">$1</span>');
            
            // null (빨간색)
            code = code.replace(/:\s*(null)/g, ': <span class="json-null">$1</span>');
            
            // 중괄호, 대괄호 (보라색)
            code = code.replace(/([{{\\}}\\[\\]])/g, '<span class="json-bracket">$1</span>');
            
            // 콜론, 쉼표 (회색)
            code = code.replace(/([,:])(?![^<]*>)/g, '<span class="json-comma">$1</span>');
            
            codeElement.innerHTML = code;
        }}
        
        // 페이지 로드 후 구문 강조 적용
        window.onload = highlightJSON;
        </script>
    </body>
    </html>
    """
    
    # JSON 길이에 따른 동적 높이 계산
    json_lines = len(formatted_json.split('\n'))
    # 기본 패딩 + 줄 수 * 줄 높이 + 여유 공간
    dynamic_height = min(max(json_lines * 24 + 60, 150), 600)
    
    # Components로 렌더링 (동적 높이)
    components.html(json_html, height=dynamic_height)

def test_result_table(test_results):
    """
    연결 테스트 결과 테이블 컴포넌트 - Components로 완전 커스터마이징
    """
    if not test_results or 'permissions' not in test_results:
        return
    
    permissions = test_results['permissions']
    
    # 테이블 제목
    st.subheader("📊 서비스별 권한 상태")
    
    # 테이블 행 생성
    table_rows = ""
    for service, has_permission in permissions.items():
        status_icon = "✅" if has_permission else "❌"
        status_text = "권한 있음" if has_permission else "권한 없음"
        status_class = "permission-success" if has_permission else "permission-failed"
        
        table_rows += f"""
        <tr>
            <td class="service-name">{service}</td>
            <td class="{status_class}">
                <span class="status-icon">{status_icon}</span>
                <span class="status-text">{status_text}</span>
            </td>
        </tr>
        """
    
    # HTML 테이블
    table_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
        }}
        .table-container {{
            background: white;
            border: 1px solid #E5E7EB;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }}
        .permission-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .permission-table th {{
            background: #F9FAFB;
            padding: 1rem;
            text-align: left;
            font-weight: 600;
            color: #374151;
            border-bottom: 1px solid #E5E7EB;
        }}
        .permission-table td {{
            padding: 0.75rem 1rem;
            border-bottom: 1px solid #F3F4F6;
        }}
        .service-name {{
            font-weight: 600;
            color: #111827;
        }}
        .permission-success {{
            color: #10B981;
        }}
        .permission-failed {{
            color: #EF4444;
        }}
        .status-icon {{
            margin-right: 0.5rem;
        }}
        .status-text {{
            font-weight: 500;
        }}
        </style>
    </head>
    <body>
        <div class="table-container">
            <table class="permission-table">
                <thead>
                    <tr>
                        <th>AWS 서비스</th>
                        <th>권한 상태</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    
    # 테이블 높이 계산 (헤더 + 행들 + 여유공간)
    table_height = len(permissions) * 50 + 100
    
    # Components로 렌더링
    components.html(table_html, height=table_height)
    
    # 요약 정보
    total_services = len(permissions)
    successful_services = sum(permissions.values())
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("전체 서비스", total_services)
    with col2:
        st.metric("권한 있음", successful_services)
    with col3:
        st.metric("권한 없음", total_services - successful_services)

def loading_spinner(message, steps=None):
    """
    로딩 스피너 + 메시지 컴포넌트
    - 연결 테스트 중 표시되는 로딩 화면
    - 진행 단계별 메시지 표시
    
    Args:
        message (str): 메인 로딩 메시지
        steps (list, optional): 진행 단계 메시지 리스트
    """
    # 기본 진행 단계
    if steps is None:
        steps = [
            "• 인증 정보 확인 중",
            "• 권한 검증 중", 
            "• 서비스 접근 가능성 확인 중"
        ]
    
    # 로딩 단계 HTML
    steps_html = ""
    for step in steps:
        steps_html += f'<div>{step}</div>'
    
    # 전체 로딩 HTML
    loading_html = f'''
    <div class="loading-container">
        <div class="loading-spinner">🔄</div>
        <div class="loading-message">{message}</div>
        <div class="loading-steps">
            {steps_html}
        </div>
    </div>
    '''
    
    st.markdown(loading_html, unsafe_allow_html=True)

def connection_test_result(test_results, test_status):
    """
    연결 테스트 결과 종합 표시 컴포넌트
    - 성공/실패/진행중 상태별로 다른 화면 표시
    - 테스트 결과 상세 정보 포함
    """
    if test_status == "idle":
        st.markdown('''
            <div class="test-result-container">
                <div class="test-icon">🔍</div>
                <div class="test-title">연결 테스트 준비</div>
                <div class="test-description">입력하신 정보로 AWS 연결을 테스트합니다.</div>
            </div>
            ''', unsafe_allow_html=True)
            
        account = st.session_state.account_data
        connection_type_label = "Cross-Account Role" if st.session_state.connection_type == "cross-account-role" else "Access Key"

        # 상단 요약 정보 박스
        st.markdown(f"""
        <div class="info-box info">
            <div style="font-size: 1.25rem;">☁️</div>
            <div class="info-box-content">
                <div class="info-box-title">연결 정보 요약</div>
                <div class="info-box-text">
                    • 환경 이름: <strong>{account['cloud_name']}</strong><br>
                    • 연결 방식: <strong>{connection_type_label}</strong><br>
                    • 계정 ID: <code>{account['account_id']}</code><br>
                    • 리전: <code>{account['primary_region']}</code><br>
                    {'• Role ARN: <code>' + account['role_arn'] + '</code><br>' if st.session_state.connection_type == 'cross-account-role' else ''}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 버튼 정렬
        col1, col2 = st.columns([1, 3])
        with col1:
            prev_clicked = st.button("🔧 설정 수정", key="test_idle_prev", use_container_width=True)
        with col2:
            test_clicked = st.button("🚀 연결 테스트 시작", key="test_idle_start", type="primary", use_container_width=True)
        
        return prev_clicked, test_clicked

    elif test_status == "testing":
        st.info("⏳ 연결을 테스트하고 있습니다...")
        return False, False

    elif test_status == "success":
        st.success("✅ 연결 성공! AWS 계정에 성공적으로 연결되었습니다.")
        return False, False

    elif test_status == "failed":
        st.error("❌ 연결 실패 - 설정을 다시 확인해주세요.")
        return False, False

def input_field_with_toggle(label, input_type="text", is_password=False, help=None):
    """
    비밀번호 토글 가능한 입력 필드 컴포넌트
    """
    if is_password:
        # 표시/숨김 상태 관리
        show_key = f"show_{label.replace(' ', '_').lower()}"
        if show_key not in st.session_state:
            st.session_state[show_key] = False
        
        col1, col2 = st.columns([4, 1])
        
        with col1:
            field_key = f"input_{label.replace(' ', '_').lower()}"
            if st.session_state[show_key]:
                value = st.text_input(label, type="default", help=help, key=field_key)
            else:
                value = st.text_input(label, type="password", help=help, key=field_key)
        
        with col2:
            st.write("")  # 라벨 높이 맞추기
            icon = "🙈" if st.session_state[show_key] else "👁️"
            if st.button(icon, key=f"toggle_{show_key}"):
                st.session_state[show_key] = not st.session_state[show_key]
                st.rerun()
        
        return value, st.session_state[show_key], False
    else:
        # 일반 텍스트 입력
        value = st.text_input(label, help=help)
        return value, False, False

def sidebar_panel():
    """
    고정 사이드바 패널 - 디버그 정보 및 확장 기능
    - 현재 상태 모니터링
    - 빠른 액션 버튼들
    - 세션 관리
    """
    with st.sidebar:
        # 헤더
        st.markdown("### 🎛️ 제어판")
        
        # 현재 상태 표시
        st.markdown("#### 📊 현재 상태")
        
        # 단계 정보
        step_names = ["시작", "연결방식선택", "권한설정", "정보입력", "테스트"]
        current_step_name = step_names[st.session_state.current_step] if st.session_state.current_step <= 4 else "완료"
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("현재 단계", f"{st.session_state.current_step}/4")
        with col2:
            st.metric("진행률", f"{(st.session_state.current_step-1)*25}%")
        
        st.info(f"📍 **{current_step_name}** 단계")
        
        # 연결 정보
        st.markdown("#### 🔗 연결 정보")
        connection_emoji = "🛡️" if st.session_state.connection_type == "cross-account-role" else "🔑"
        st.write(f"{connection_emoji} **연결방식:** {st.session_state.connection_type}")
        st.write(f"🔄 **연결상태:** {st.session_state.connection_status}")
        
        if st.session_state.account_data.get('cloud_name'):
            st.write(f"☁️ **환경명:** {st.session_state.account_data['cloud_name']}")
        
        # 구분선
        st.divider()
        
        # 빠른 액션
        st.markdown("#### ⚡ 빠른 액션")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⏮️ 처음으로", use_container_width=True):
                st.session_state.current_step = 1
                st.rerun()
        
        with col2:
            if st.session_state.current_step > 1:
                if st.button("⬅️ 이전단계", use_container_width=True):
                    st.session_state.current_step -= 1
                    st.rerun()
        
        if st.session_state.current_step < 4:
            if st.button("➡️ 다음단계", use_container_width=True):
                st.session_state.current_step += 1
                st.rerun()
        
        # 구분선
        st.divider()
        
        # 세션 관리
        st.markdown("#### 🔧 세션 관리")
        
        if st.button("🔄 전체 초기화", type="secondary", use_container_width=True):
            # 안전한 초기화
            reset_session_state(keep_aws_handler=False)
            st.session_state.clear()  # 완전 초기화
            st.rerun()
        
        # 데이터 내보내기
        if st.session_state.account_data:
            st.download_button(
                "📥 설정 다운로드",
                data=json.dumps(st.session_state.account_data, indent=2, ensure_ascii=False),
                file_name="aws_connection_settings.json",
                mime="application/json",
                use_container_width=True
            )
        
        # 구분선
        st.divider()
        
        # 디버그 정보 (접을 수 있게)
        with st.expander("🐛 디버그 정보", expanded=False):
            # 실제 Secret Key 길이 계산
            actual_secret = st.session_state.get('temp_secret_key', '') 
            if not actual_secret:
                stored_secret = st.session_state.account_data.get('secret_access_key', '')
                actual_secret = stored_secret if stored_secret != '[MASKED]' else ''

            debug_info = {
                "current_step": st.session_state.current_step,
                "connection_type": st.session_state.connection_type,
                "connection_status": st.session_state.connection_status,
                "account_data": {
                    "cloud_name": st.session_state.account_data.get('cloud_name', ''),
                    "account_id": st.session_state.account_data.get('account_id', ''),
                    "access_key_length": len(st.session_state.account_data.get('access_key_id', '')),
                    "secret_key_length": len(actual_secret),
                    "secret_key_status": "temp_stored" if st.session_state.get('temp_secret_key') else ("masked" if st.session_state.account_data.get('secret_access_key') == '[MASKED]' else "direct"),
                    "region": st.session_state.account_data.get('primary_region', '')
                }
            }
            st.json(debug_info)
            
def navigation_buttons(show_prev=True, show_next=True, prev_label="이전", next_label="다음", 
                      next_disabled=False, prev_callback=None, next_callback=None):
    """
    네비게이션 버튼 컴포넌트
    - 이전/다음 단계 이동 버튼
    - 조건부 활성화/비활성화 지원
    
    Args:
        show_prev (bool): 이전 버튼 표시 여부
        show_next (bool): 다음 버튼 표시 여부
        prev_label (str): 이전 버튼 라벨
        next_label (str): 다음 버튼 라벨
        next_disabled (bool): 다음 버튼 비활성화 여부
        prev_callback (callable): 이전 버튼 콜백
        next_callback (callable): 다음 버튼 콜백
    
    Returns:
        tuple: (이전버튼클릭여부, 다음버튼클릭여부)
    """
    col1, col2, col3 = st.columns([1, 2, 1])
    
    prev_clicked = False
    next_clicked = False
    
    with col1:
        if show_prev:
            prev_clicked = st.button(
                f"← {prev_label}", 
                type="secondary",
                use_container_width=True
            )
            if prev_clicked and prev_callback:
                prev_callback()
    
    with col3:
        if show_next:
            next_clicked = st.button(
                f"{next_label} →", 
                type="primary",
                disabled=next_disabled,
                use_container_width=True
            )
            if next_clicked and next_callback:
                next_callback()
    
    return prev_clicked, next_clicked

def reset_session_state(keep_aws_handler=True):
    """
    세션 상태 초기화 공통 함수 - 중복 방지 개선
    
    Args:
        keep_aws_handler (bool): AWS 핸들러 유지 여부
    """
    # 현재 세션에서 삭제할 키들 수집
    keys_to_delete = []
    for key in list(st.session_state.keys()):
        if key.startswith(('current_step', 'connection_type', 'account_data', 
                          'connection_status', 'test_results', 'show_')):
            keys_to_delete.append(key)
    
    # 안전하게 삭제
    for key in keys_to_delete:
        if key in st.session_state:
            del st.session_state[key]
    
    # 기본값으로 재초기화 (한 번에 설정)
    default_state = {
        'current_step': 1,
        'connection_type': 'cross-account-role',
        'account_data': {
            'cloud_name': '',
            'account_id': '',
            'role_arn': '',
            'external_id': '',
            'access_key_id': '',
            'secret_access_key': '',
            'primary_region': 'ap-northeast-2',
            'contact_email': ''
        },
        'connection_status': 'idle',
        'test_results': None
    }
    
    # 한 번에 업데이트
    st.session_state.update(default_state)
    
    # AWS 핸들러 설정
    if keep_aws_handler and 'aws_handler' not in st.session_state:
        st.session_state.aws_handler = AWSConnectionHandler()

def validate_and_show_error(field_name, value, validator_func):
    """
    입력값 검증 후 에러 메시지 자동 표시
    
    Args:
        field_name (str): 필드명 (에러 키로 사용)
        value (str): 검증할 값
        validator_func (callable): 검증 함수
    
    Returns:
        bool: 검증 성공 여부
    """
    if not value:
        return True  # 빈 값은 별도 처리하지 않음
    
    is_valid, error_msg = validator_func(value)
    
    if not is_valid:
        st.error(f"❌ {error_msg}")
        return False
    
    return True

def safe_session_update(updates):
    """
    세션 상태 안전 업데이트
    - 중복 업데이트 방지
    
    Args:
        updates (dict): 업데이트할 세션 상태들
    """
    for key, value in updates.items():
        if key not in st.session_state or st.session_state[key] != value:
            st.session_state[key] = value

def get_session_state_summary():
    """
    현재 세션 상태 요약 반환
    - 디버깅용
    """
    return {
        'step': st.session_state.get('current_step', 'unknown'),
        'connection_type': st.session_state.get('connection_type', 'unknown'),
        'connection_status': st.session_state.get('connection_status', 'unknown'),
        'has_account_data': bool(st.session_state.get('account_data', {})),
        'has_test_results': bool(st.session_state.get('test_results')),
        'total_session_keys': len(st.session_state.keys())
    }

def get_actual_secret_key():
    """실제 Secret Key 반환 (마스킹되지 않은)"""
    temp_key = st.session_state.get('temp_secret_key', '')
    stored_key = st.session_state.account_data.get('secret_access_key', '')
    
    if temp_key:
        return temp_key
    elif stored_key and stored_key != '[MASKED]':
        return stored_key
    else:
        return ''

def cleanup_sensitive_data():
    """민감 정보 정리"""
    if 'temp_secret_key' in st.session_state:
        del st.session_state.temp_secret_key
    
    if 'account_data' in st.session_state:
        if st.session_state.account_data.get('secret_access_key') != '[MASKED]':
            st.session_state.account_data['secret_access_key'] = '[MASKED]'
            