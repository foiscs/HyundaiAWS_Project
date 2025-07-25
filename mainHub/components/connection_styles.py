"""
WALB Connection CSS 스타일 모듈
모든 Connection 관련 CSS 스타일을 중앙 집중 관리

Functions:
- inject_custom_font: 전체 폰트 설정
- inject_custom_button_style: 커스텀 버튼 스타일
- inject_expander_style: Streamlit expander 스타일
- get_main_styles: 메인 페이지 기본 스타일
- get_all_styles: 모든 스타일 통합 반환

Note: 이 파일은 diagnosis와 공통으로 사용되는 기본 스타일들을 포함
"""

def inject_custom_font():
    """전체 폰트 설정 - 모든 Streamlit 요소에 Pretendard 강제 적용"""
    return """
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');
    
    /* 최상위 우선순위로 전역 폰트 강제 적용 */
    *, *::before, *::after,
    html, body, div, span, h1, h2, h3, h4, h5, h6, p, a, em, img, strong, sub, sup, ol, ul, li, fieldset, form, label, legend, table, caption, tbody, tfoot, thead, tr, th, td, article, aside, canvas, details, embed, figure, figcaption, footer, header, hgroup, menu, nav, output, ruby, section, summary, time, mark, audio, video, input, textarea, select, option, button {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', sans-serif !important;
        font-weight: inherit !important;
    }
    
    /* Streamlit 클래스 기반 강제 적용 */
    [class*="css"], [class*="st"], [class*="streamlit"] {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', sans-serif !important;
    }
    
    /* Streamlit data-testid 기반 강제 적용 */
    [data-testid] *,
    div[data-testid="stSidebar"] *,
    div[data-testid="stMain"] *,
    div[data-testid="stHeader"] *,
    div[data-testid="stButton"] *,
    div[data-testid="stSelectbox"] *,
    div[data-testid="stRadio"] *,
    div[data-testid="stTextInput"] *,
    div[data-testid="stTextArea"] *,
    div[data-testid="stExpander"] *,
    div[data-testid="stExpanderHeader"] *,
    div[data-testid="stExpanderDetails"] *,
    div[data-testid="stMarkdown"] *,
    div[data-testid="stMetric"] *,
    div[data-testid="metric-container"] * {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', sans-serif !important;
    }
    
    /* 동적으로 생성되는 Streamlit 요소들 */
    .stButton > button,
    .stSelectbox > div,
    .stRadio > div,
    .stTextInput > div,
    .stTextArea > div,
    .stExpander > div,
    .stMarkdown,
    .stMetric {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', sans-serif !important;
    }
    
    .main > div {
        padding-top: 2rem;
    }
    </style>
    """

def inject_custom_button_style():
    """커스텀 버튼 스타일"""
    return """
    <style>
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stButton > button:hover {
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        transform: translateY(-1px);
    }
    
    .stButton > button:active {
        transform: translateY(0px);
    }
    
    /* Primary 버튼 */
    div[data-testid="column"] .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    }
    
    div[data-testid="column"] .stButton > button[kind="primary"]:hover {
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }
    
    /* Secondary 버튼 */
    div[data-testid="column"] .stButton > button[kind="secondary"] {
        background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
        color: #374151;
    }
    
    div[data-testid="column"] .stButton > button[kind="secondary"]:hover {
        box-shadow: 0 4px 12px rgba(107, 114, 128, 0.2);
    }
    </style>
    """

def inject_expander_style():
    """Streamlit expander 커스터마이징"""
    return """
    <style>
    .streamlit-expanderHeader {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 0.75rem;
        border: 1px solid #e9ecef;
        font-weight: 500;
    }
    
    .streamlit-expanderContent {
        border: 1px solid #e9ecef;
        border-top: none;
        border-radius: 0 0 8px 8px;
        padding: 1rem;
        background-color: white;
    }
    </style>
    """

def get_sidebar_navigation_styles():
    """사이드바 네비게이션 스타일"""
    return """
    <style>
    /* 사이드바 스타일 */
    .css-1d391kg {
        background-color: #f8fafc;
    }
    
    /* 사이드바 네비게이션 스타일 */
    .stSidebar {
        background-color: #f8fafc;
    }
    
    /* 사이드바 네비게이션 링크 스타일 */
    .stSidebar [data-testid="stSidebarNav"] ul {
        padding: 0;
        margin: 0;
        list-style: none;
        background: white;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        padding: 0.5rem;
        margin-bottom: 1rem;
    }
    
    .stSidebar [data-testid="stSidebarNav"] ul li {
        margin: 0.25rem 0;
    }
    
    .stSidebar [data-testid="stSidebarNav"] ul li a {
        display: flex;
        align-items: center;
        padding: 0.75rem 1rem;
        text-decoration: none;
        color: #475569;
        border-radius: 8px;
        transition: all 0.2s ease;
        font-weight: 500;
        font-size: 0.95rem;
        position: relative;
        overflow: hidden;
    }
    
    .stSidebar [data-testid="stSidebarNav"] ul li a:before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        height: 100%;
        width: 4px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        transform: scaleY(0);
        transition: transform 0.2s ease;
    }
    
    .stSidebar [data-testid="stSidebarNav"] ul li a:hover {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        transform: translateX(4px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    .stSidebar [data-testid="stSidebarNav"] ul li a:hover:before {
        transform: scaleY(1);
    }
    
    /* 활성 페이지 스타일 */
    .stSidebar [data-testid="stSidebarNav"] ul li a[aria-current="page"] {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
        transform: translateX(4px);
    }
    
    .stSidebar [data-testid="stSidebarNav"] ul li a[aria-current="page"]:before {
        transform: scaleY(1);
        background: rgba(255, 255, 255, 0.3);
    }
    
    /* 각 페이지별 아이콘 추가 */
    .stSidebar [data-testid="stSidebarNav"] ul li a[href="/"]::before {
        content: "🏠 ";
        margin-right: 0.5rem;
    }
    
    .stSidebar [data-testid="stSidebarNav"] ul li a[href="/connection"]::before {
        content: "🔗 ";
        margin-right: 0.5rem;
    }
    
    .stSidebar [data-testid="stSidebarNav"] ul li a[href="/connection_backup"]::before {
        content: "🔗📋 ";
        margin-right: 0.5rem;
    }
    
    .stSidebar [data-testid="stSidebarNav"] ul li a[href="/diagnosis"]::before {
        content: "🛡️ ";
        margin-right: 0.5rem;
    }
    
    .stSidebar [data-testid="stSidebarNav"] ul li a[href="/diagnosis_backup"]::before {
        content: "🛡️📋 ";
        margin-right: 0.5rem;
    }
    </style>
    """


def get_main_styles():
    """메인 페이지 기본 스타일"""
    return """
    <style>
    /* 메인 컨테이너 */
    .main-container {
        width: 100%;
        padding: 1.5rem;
    }
    
    /* 제목 스타일 */
    .main-title {
        color: #111827;
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    
    .stMainBlockContainer {
        padding-top: 5rem !important;
    }
    
    /* 일반적인 카드 스타일 */
    .stContainer > div {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    
    /* 입력 필드 스타일 */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 1px solid #d1d5db;
        padding: 0.75rem;
        font-size: 0.9rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    
    /* 선택 박스 스타일 */
    .stSelectbox > div > div > div {
        border-radius: 8px;
        border: 1px solid #d1d5db;
    }
    
    /* 성공/오류 메시지 스타일 */
    .stSuccess {
        background-color: #f0f9ff;
        border: 1px solid #0ea5e9;
        border-radius: 8px;
        padding: 1rem;
    }
    
    .stError {
        background-color: #fef2f2;
        border: 1px solid #ef4444;
        border-radius: 8px;
        padding: 1rem;
    }
    
    .stWarning {
        background-color: #fffbeb;
        border: 1px solid #f59e0b;
        border-radius: 8px;
        padding: 1rem;
    }
    
    .stInfo {
        background-color: #f0f9ff;
        border: 1px solid #3b82f6;
        border-radius: 8px;
        padding: 1rem;
    }
    
    /* 메트릭 컨테이너 스타일 */
    div[data-testid="metric-container"] {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    /* 컬럼 간격 조정 */
    .row-widget.stRadio > div {
        flex-direction: row;
        gap: 1rem;
    }
    
    /* 코드 블록 스타일 */
    .stCode {
        background-color: #1f2937;
        border-radius: 8px;
        padding: 1rem;
    }
    
    /* 마크다운 스타일 개선 */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #1f2937;
        font-weight: 600;
    }
    
    .stMarkdown h1 {
        border-bottom: 2px solid #e5e7eb;
        padding-bottom: 0.5rem;
    }
    
    .stMarkdown h3 {
        color: #374151;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    
    /* 구분선 스타일 */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(to right, transparent, #e5e7eb, transparent);
        margin: 2rem 0;
    }
    
    /* 로딩 스타일 */
    .stSpinner > div {
        border-top-color: #3b82f6;
    }
    
    /* 토글 버튼 스타일 */
    .stCheckbox > label {
        background-color: #f3f4f6;
        padding: 0.5rem;
        border-radius: 6px;
        border: 1px solid #d1d5db;
    }
    
    .stCheckbox > label:hover {
        background-color: #e5e7eb;
    }
    
    /* 프로그레스 바 스타일 */
    .stProgress > div > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 4px;
    }
    
    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        padding: 0 1.5rem;
        background-color: #f3f4f6;
        border-radius: 8px;
        color: #6b7280;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* 데이터프레임 스타일 */
    .stDataFrame {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* 파일 업로더 스타일 */
    .stFileUploader > div {
        border: 2px dashed #d1d5db;
        border-radius: 8px;
        padding: 2rem;
        text-align: center;
        background-color: #f9fafb;
    }
    
    .stFileUploader > div:hover {
        border-color: #3b82f6;
        background-color: #f0f9ff;
    }
    
    /* 알림 배너 스타일 */
    .stAlert {
        border-radius: 8px;
        border: 1px solid;
        padding: 1rem;
        margin: 1rem 0;
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

def get_all_styles():
    """모든 스타일 통합 반환"""
    return (
        inject_custom_font() +
        get_force_pretendard_font() +
        inject_custom_button_style() +
        inject_expander_style() +
        get_sidebar_navigation_styles() +
        get_main_styles()
    )