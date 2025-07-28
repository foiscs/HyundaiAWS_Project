"""
WALB 진단 페이지 CSS 스타일 모듈
모든 진단 관련 CSS 스타일을 중앙 집중 관리

Functions:
- get_diagnosis_hero_styles(): 히어로 헤더 스타일 (그라데이션, 애니메이션)
- get_diagnosis_card_styles(): 진단 카드 스타일 (항목 정보 표시)
- get_diagnosis_progress_styles(): 진단 진행 스타일 (로딩 애니메이션)
- get_diagnosis_result_styles(): 결과 표시 스타일 (위험도 배지)
- get_diagnosis_layout_styles(): 레이아웃 스타일 (반응형, 여백 조정)
- get_diagnosis_account_card_styles(): 계정 카드 스타일 (정보 카드)
- get_all_diagnosis_styles(): 모든 스타일 통합 반환
"""

def get_diagnosis_hero_styles():
    """히어로 헤더 스타일 - 그라데이션 배경과 부유 애니메이션 포함"""
    return """
    <style>
    .hero-header {
        background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
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
        background: linear-gradient(45deg, #ffffff, #cbd5e0);
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
    .floating-elements {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        pointer-events: none;
        overflow: hidden;
    }
    .floating-circle {
        position: absolute;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 50%;
        animation: float-circle 6s ease-in-out infinite;
    }
    .circle-1 {
        width: 60px;
        height: 60px;
        top: 20%;
        right: 10%;
        animation-delay: 0s;
    }
    .circle-2 {
        width: 40px;
        height: 40px;
        top: 60%;
        right: 20%;
        animation-delay: 2s;
    }
    .circle-3 {
        width: 80px;
        height: 80px;
        top: 10%;
        left: 15%;
        animation-delay: 4s;
    }
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
    @keyframes float-circle {
        0%, 100% { transform: translateY(0px) scale(1); opacity: 0.3; }
        50% { transform: translateY(-20px) scale(1.1); opacity: 0.6; }
    }
    </style>
    """

def get_diagnosis_card_styles():
    """진단 항목 카드 스타일 - 진단 정보 표시용 카드 디자인"""
    return """
    <style>
    .diagnosis-card {
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        transition: all 0.2s ease;
    }
    .diagnosis-card:hover {
        background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
        transform: translateY(-1px);
    }
    .diagnosis-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 8px;
    }
    .diagnosis-description {
        color: #4a5568;
        font-size: 0.9rem;
        margin-bottom: 12px;
    }
    .diagnosis-meta {
        display: flex;
        align-items: center;
        gap: 16px;
        margin-bottom: 12px;
    }
    </style>
    """

def get_diagnosis_progress_styles():
    """진단 진행 상태 스타일 - 로딩 스피너와 진행 표시"""
    return """
    <style>
    .diagnosis-progress {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 24px;
        margin: 16px 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        border: none;
        box-shadow: 0 8px 16px rgba(102, 126, 234, 0.25);
        color: white;
        position: relative;
        overflow: hidden;
    }
    .diagnosis-progress::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="dots" width="10" height="10" patternUnits="userSpaceOnUse"><circle cx="5" cy="5" r="1" fill="rgba(255,255,255,0.1)"/></pattern></defs><rect width="100" height="100" fill="url(%23dots)"/></svg>');
        opacity: 0.5;
    }
    .diagnosis-progress > * {
        position: relative;
        z-index: 2;
    }
    .progress-icon {
        font-size: 2rem;
        animation: spin 2s linear infinite;
        margin-bottom: 12px;
    }
    .progress-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: white;
        text-align: center;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    .progress-subtitle {
        font-size: 1rem;
        color: rgba(255, 255, 255, 0.9);
        text-align: center;
        margin-top: 6px;
        text-shadow: 0 1px 2px rgba(0,0,0,0.2);
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    </style>
    """

def get_diagnosis_result_styles():
    """진단 결과 표시 스타일 - 위험도별 배지와 메트릭 컨테이너"""
    return """
    <style>
    .risk-badge {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 0.9rem;
        margin-top: 8px;
        box-sizing: border-box;
    }
    .risk-high {
        background-color: #e53e3e15;
        border: 1px solid #e53e3e40;
        color: #e53e3e;
    }
    .risk-medium {
        background-color: #dd6b2015;
        border: 1px solid #dd6b2040;
        color: #dd6b20;
    }
    .risk-low {
        background-color: #38a16915;
        border: 1px solid #38a16940;
        color: #38a169;
    }
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%) !important;
        border: 1px solid #cbd5e0 !important;
        border-radius: 10px !important;
        padding: 16px !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08) !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="metric-container"]:hover {
        background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%) !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.12) !important;
        transform: translateY(-1px) !important;
    }
    </style>
    """

def get_diagnosis_layout_styles():
    """진단 페이지 레이아웃 스타일 - 반응형 레이아웃과 여백 조정"""
    return """
    <style>
    .scroll-target {
        scroll-margin-top: 100px;
    }
    div[data-testid="stExpanderDetails"] {
        padding-top: 0 !important;
    }
    .stExpander {
        margin-bottom: 0.1rem !important;
    }
    .streamlit-expanderHeader {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border-radius: 10px !important;
        padding: 12px 16px !important;
        border: none !important;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3) !important;
        transition: all 0.2s ease !important;
    }
    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%) !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4) !important;
        transform: translateY(-1px) !important;
    }
    
    /* JavaScript로 동적 추가되는 중요도별 클래스 스타일 */
    /* 상 위험도 - 빨간색 계열 */
    .streamlit-expanderHeader.importance-high {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
        box-shadow: 0 2px 8px rgba(239, 68, 68, 0.3) !important;
    }
    .streamlit-expanderHeader.importance-high:hover {
        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%) !important;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4) !important;
    }
    
    /* 중 위험도 - 주황색 계열 */
    .streamlit-expanderHeader.importance-medium {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%) !important;
        box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3) !important;
    }
    .streamlit-expanderHeader.importance-medium:hover {
        background: linear-gradient(135deg, #d97706 0%, #b45309 100%) !important;
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.4) !important;
    }
    
    /* 하 위험도 - 초록색 계열 */
    .streamlit-expanderHeader.importance-low {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3) !important;
    }
    .streamlit-expanderHeader.importance-low:hover {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4) !important;
    }
    .streamlit-expanderContent {
        background: linear-gradient(135deg, #fafbff 0%, #f7fafc 100%) !important;
        border: 1px solid #e2e8f0 !important;
        border-top: none !important;
        border-radius: 0 0 10px 10px !important;
        padding: 20px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
    }
    div[data-testid="stRadio"] {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        height: 38px !important;
    }
    div[data-testid="stRadio"] > div {
        display: flex !important;
        align-items: center !important;
        height: 100% !important;
        gap: 20px !important;
    }
    div[data-testid="stVerticalBlock"][data-test-scroll-behavior="normal"] {
        margin-top: 0.25rem !important;
    }
    .stVerticalBlock[data-testid="stVerticalBlock"] {
        margin-top: 0.25rem !important;
    }
    div[direction="column"][height="100%"][data-testid="stVerticalBlock"] {
        margin-top: 0 !important;
    }
    div[direction="column"][height="100%"][data-testid="stVerticalBlock"]:has(.stButton) {
        margin-top: 0.5rem !important;
    }
    </style>
    """

def get_diagnosis_account_card_styles():
    """계정 정보 카드 스타일 - 주요 카드와 일반 카드 스타일 구분"""
    return """
    <style>
    .account-info-card {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        padding: 16px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .account-info-label {
        font-size: 0.7rem;
        color: #6c757d;
        margin-bottom: 4px;
    }
    .account-info-value {
        font-size: 0.9rem;
        font-weight: 600;
        color: #495057;
    }
    .account-primary-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 16px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .account-primary-label {
        font-size: 0.7rem;
        opacity: 0.8;
        margin-bottom: 4px;
    }
    .account-primary-value {
        font-size: 1.1rem;
        font-weight: bold;
    }
    </style>
    """

def get_force_pretendard_font():
    """Pretendard 폰트 강제 적용 - 모든 Streamlit 요소 오버라이드"""
    return """
    <style>
    /* 최우선 Pretendard 폰트 강제 적용 */
    *, *::before, *::after {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
    }
    
    /* Streamlit 기본 폰트 오버라이드 */
    .css-10trblm, .css-1d391kg, .css-1cpxqw2, .css-1avcm0n,
    .css-145kmo2, .css-1544g2n, .css-1y4p8pa, .css-17lntkn,
    .css-1aumxhk, .css-1629p8f, .css-19ih9d0, .css-17eq0hr {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
    }
    
    /* 모든 텍스트 요소 강제 오버라이드 */
    input, textarea, select, option, label, button, span, div, p, h1, h2, h3, h4, h5, h6, li, ul, ol, table, td, th, a {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
    }
    </style>
    """

def get_all_diagnosis_styles():
    """모든 진단 관련 스타일 통합 반환 - 공통 스타일과 진단 전용 스타일 결합"""
    # connection_styles.py의 공통 스타일들을 import
    from .connection_styles import inject_custom_font, inject_custom_button_style, inject_expander_style, get_sidebar_navigation_styles
    
    return (
        inject_custom_font() +
        get_force_pretendard_font() +
        inject_custom_button_style() +
        inject_expander_style() +
        get_sidebar_navigation_styles() +
        get_diagnosis_hero_styles() +
        get_diagnosis_card_styles() +
        get_diagnosis_progress_styles() +
        get_diagnosis_result_styles() +
        get_diagnosis_layout_styles() +
        get_diagnosis_account_card_styles()
    )