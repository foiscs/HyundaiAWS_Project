"""
WALB Connection HTML 템플릿 모듈
모든 Connection 관련 HTML 템플릿을 중앙 집중 관리

Functions:
- get_hero_header_template: 메인 헤더 HTML 템플릿
- get_step_indicator_template: 단계 표시기 HTML 템플릿
- get_connection_type_card_template: 연결방식 선택 카드 템플릿
- get_info_box_template: 정보/경고 박스 템플릿
- get_json_code_block_template: JSON 코드 블록 템플릿
- get_test_result_table_template: 연결 테스트 결과 테이블 템플릿
- get_loading_spinner_template: 로딩 스피너 템플릿
- get_navigation_buttons_template: 네비게이션 버튼 템플릿
"""

def get_hero_header_template() -> str:
    """메인 헤더 HTML 템플릿 반환"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');
        
        body {
            margin: 0;
            padding: 0;
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', sans-serif;
        }
        .hero-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2.5rem 2rem;
            border-radius: 16px;
            margin: 1rem 0 2rem 0;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            position: relative;
            overflow: hidden;
        }
        .hero-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
            opacity: 0.3;
        }
        .hero-content {
            position: relative;
            z-index: 2;
            display: flex;
            align-items: center;
            gap: 1.5rem;
        }
        .hero-icon {
            font-size: 3.5rem;
            filter: drop-shadow(0 4px 8px rgba(0,0,0,0.2));
            animation: float 3s ease-in-out infinite;
        }
        .hero-text {
            flex: 1;
        }
        .hero-title {
            font-size: 2.25rem;
            font-weight: 700;
            margin: 0 0 0.5rem 0;
            background: linear-gradient(45deg, #ffffff, #e0e7ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .hero-subtitle {
            font-size: 1.1rem;
            opacity: 0.9;
            margin: 0;
            font-weight: 400;
        }
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
        }
        </style>
    </head>
    <body>
        <div class="hero-header">
            <div class="hero-content">
                <div class="hero-icon">☁️</div>
                <div class="hero-text">
                    <h1 class="hero-title">AWS 계정 연결</h1>
                    <p class="hero-subtitle">클라우드 보안 진단을 위한 계정 설정</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

def get_step_indicator_template(step_items_html: str) -> str:
    """단계 표시기 HTML 템플릿 반환"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', sans-serif;
        }}
        .step-container {{
            background: white;
            border: 1px solid #F9FAFB;
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

def get_connection_type_card_template(title: str, description: str, pros: str, is_selected: bool, icon: str, security_level: str) -> str:
    """연결방식 선택 카드 HTML 템플릿 반환"""
    selected_class = "card-selected" if is_selected else ""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', sans-serif;
        }}
        .connection-card {{
            border: 2px solid #e5e7eb;
            border-radius: 12px;
            padding: 1.5rem;
            background: white;
            transition: all 0.3s ease;
            cursor: pointer;
            height: 100%;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }}
        .connection-card:hover {{
            border-color: #3b82f6;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
        }}
        .card-selected {{
            border-color: #3b82f6 !important;
            background: #f8faff !important;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15) !important;
        }}
        .card-header {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 1rem;
        }}
        .card-icon {{
            font-size: 2rem;
        }}
        .card-title {{
            font-size: 1.125rem;
            font-weight: 600;
            color: #1f2937;
        }}
        .security-badge {{
            background: #10b981;
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            font-size: 0.75rem;
            font-weight: 500;
            margin-left: auto;
        }}
        .card-description {{
            color: #6b7280;
            font-size: 0.875rem;
            margin-bottom: 1rem;
            line-height: 1.5;
        }}
        .card-pros {{
            color: #374151;
            font-size: 0.875rem;
            line-height: 1.5;
        }}
        </style>
    </head>
    <body>
        <div class="connection-card {selected_class}">
            <div class="card-header">
                <span class="card-icon">{icon}</span>
                <span class="card-title">{title}</span>
                <span class="security-badge">{security_level}</span>
            </div>
            <div class="card-description">{description}</div>
            <div class="card-pros">{pros}</div>
        </div>
    </body>
    </html>
    """

def get_info_box_template(message: str, box_type: str, title: str = "", icon: str = "") -> str:
    """정보/경고 박스 HTML 템플릿 반환"""
    type_styles = {
        'info': {'bg': '#e1f5fe', 'border': '#0288d1', 'color': '#01579b', 'icon': 'ℹ️'},
        'warning': {'bg': '#fff8e1', 'border': '#ffa000', 'color': '#e65100', 'icon': '⚠️'},
        'error': {'bg': '#ffebee', 'border': '#d32f2f', 'color': '#b71c1c', 'icon': '❌'},
        'success': {'bg': '#e8f5e8', 'border': '#4caf50', 'color': '#2e7d32', 'icon': '✅'}
    }
    
    style = type_styles.get(box_type, type_styles['info'])
    display_icon = icon if icon else style['icon']
    
    title_html = f"<div class='info-title'>{display_icon} {title}</div>" if title else ""
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', sans-serif;
        }}
        .info-box {{
            background-color: {style['bg']};
            border: 1px solid {style['border']};
            border-radius: 8px;
            padding: 1rem;
            margin: 0.25rem 0;
            color: {style['color']};
        }}
        .info-title {{
            font-weight: 600;
            margin-bottom: 0.5rem;
            font-size: 0.95rem;
        }}
        .info-message {{
            font-size: 0.9rem;
            line-height: 1.5;
        }}
        </style>
    </head>
    <body>
        <div class="info-box">
            {title_html}
            <div class="info-message">{message}</div>
        </div>
    </body>
    </html>
    """

def get_json_code_block_template(formatted_json: str, title: str) -> str:
    """JSON 코드 블록 HTML 템플릿 반환"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', sans-serif;
        }}
        .json-container {{
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            margin: 1rem 0;
        }}
        .json-header {{
            background: #6c757d;
            color: white;
            padding: 0.75rem 1rem;
            border-radius: 8px 8px 0 0;
            font-weight: 500;
            font-size: 0.9rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .copy-button {{
            background: rgba(255, 255, 255, 0.2);
            border: none;
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.8rem;
        }}
        .copy-button:hover {{
            background: rgba(255, 255, 255, 0.3);
        }}
        .json-content {{
            padding: 1rem;
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif;
            font-size: 0.85rem;
            line-height: 1.4;
            white-space: pre-wrap;
            overflow-x: auto;
            background: white;
            border-radius: 0 0 8px 8px;
        }}
        .json-string {{ color: #d63384; }}
        .json-number {{ color: #0d6efd; }}
        .json-boolean {{ color: #6f42c1; }}
        .json-null {{ color: #6c757d; }}
        .json-key {{ color: #198754; font-weight: 500; }}
        </style>
    </head>
    <body>
        <div class="json-container">
            <div class="json-header">
                <span>{title}</span>
                <button class="copy-button" onclick="copyToClipboard()">📋 복사</button>
            </div>
            <div class="json-content" id="jsonContent">{formatted_json}</div>
        </div>
        <script>
        function copyToClipboard() {{
            const content = document.getElementById('jsonContent').textContent;
            navigator.clipboard.writeText(content).then(function() {{
                alert('JSON이 클립보드에 복사되었습니다!');
            }});
        }}
        </script>
    </body>
    </html>
    """

def get_test_result_table_template(table_rows_html: str) -> str:
    """연결 테스트 결과 테이블 HTML 템플릿 반환"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', sans-serif;
        }}
        .test-table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }}
        .test-table th {{
            background-color: #f8f9fa;
            color: #495057;
            font-weight: 600;
            padding: 12px 16px;
            text-align: left;
            border-bottom: 2px solid #dee2e6;
            font-size: 0.9rem;
        }}
        .test-table td {{
            padding: 12px 16px;
            border-bottom: 1px solid #e9ecef;
            font-size: 0.85rem;
        }}
        .test-table tr:last-child td {{
            border-bottom: none;
        }}
        .test-table tr:hover {{
            background-color: #f8f9fa;
        }}
        .status-success {{
            color: #28a745;
            font-weight: 500;
        }}
        .status-failed {{
            color: #dc3545;
            font-weight: 500;
        }}
        .status-pending {{
            color: #6c757d;
            font-weight: 500;
        }}
        </style>
    </head>
    <body>
        <table class="test-table">
            <thead>
                <tr>
                    <th>AWS 서비스</th>
                    <th>권한 상태</th>
                    <th>테스트 결과</th>
                    <th>응답 시간</th>
                </tr>
            </thead>
            <tbody>
                {table_rows_html}
            </tbody>
        </table>
    </body>
    </html>
    """

def get_loading_spinner_template(message: str) -> str:
    """로딩 스피너 HTML 템플릿 반환"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', sans-serif;
        }}
        .loading-container {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 2rem;
            background: #f8f9fa;
            border-radius: 8px;
            margin: 1rem 0;
        }}
        .loading-spinner {{
            font-size: 3rem;
            animation: spin 2s linear infinite;
            margin-bottom: 1rem;
        }}
        .loading-message {{
            color: #495057;
            font-size: 1rem;
            text-align: center;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        </style>
    </head>
    <body>
        <div class="loading-container">
            <div class="loading-spinner">🔄</div>
            <div class="loading-message">{message}</div>
        </div>
    </body>
    </html>
    """

def get_navigation_buttons_template(show_prev: bool, show_next: bool, prev_text: str = "이전", next_text: str = "다음", next_disabled: bool = False) -> str:
    """네비게이션 버튼 HTML 템플릿 반환"""
    prev_button = f"""
        <button class="nav-button nav-button-secondary" onclick="window.parent.postMessage('prev_step', '*')">
            ← {prev_text}
        </button>
    """ if show_prev else ""
    
    next_button_class = "nav-button nav-button-primary" + (" nav-button-disabled" if next_disabled else "")
    next_button = f"""
        <button class="{next_button_class}" onclick="window.parent.postMessage('next_step', '*')" {'disabled' if next_disabled else ''}>
            {next_text} →
        </button>
    """ if show_next else ""
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', sans-serif;
        }}
        .nav-container {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem 0;
            gap: 1rem;
        }}
        .nav-button {{
            padding: 0.75rem 1.5rem;
            border-radius: 6px;
            border: none;
            font-size: 0.9rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .nav-button-primary {{
            background-color: #3b82f6;
            color: white;
        }}
        .nav-button-primary:hover {{
            background-color: #2563eb;
        }}
        .nav-button-secondary {{
            background-color: #f3f4f6;
            color: #374151;
            border: 1px solid #d1d5db;
        }}
        .nav-button-secondary:hover {{
            background-color: #e5e7eb;
        }}
        .nav-button-disabled {{
            background-color: #9ca3af !important;
            cursor: not-allowed !important;
        }}
        .nav-button-disabled:hover {{
            background-color: #9ca3af !important;
        }}
        </style>
    </head>
    <body>
        <div class="nav-container">
            <div>{prev_button}</div>
            <div>{next_button}</div>
        </div>
    </body>
    </html>
    """